from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Self
from discord import Guild, Member, TextChannel
from src.channels import DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.roles import has_role, HIVE_MXTRESS
from src.db.record import Record
from src.db.database import fetchcolumn
from src.db.timer import Timer


@dataclass(frozen=True)
class BatteryType(Record):
    table = 'battery_types'
    '''
    The database table name.
    '''

    id: int
    '''
    The primary key.
    '''

    name: str
    '''
    The type name, e.g. "Medium".
    '''

    capacity: int
    '''
    The battery's duration, in minutes.
    '''

    recharge_rate: int
    '''
    The battery's recharge rate, in minutes of capacity gained per hour of recharge.
    '''


@dataclass
class Storage(Record):
    table = 'storage'
    '''
    The database table name.
    '''

    id: str
    '''
    The unique ID of the storage record.
    '''

    stored_by: int | None
    '''
    The Discord ID of the user that initiated the storage. None for Hive Mxtress.
    '''

    target_id: int
    '''
    The Discord ID of the drone that was stored.
    '''

    purpose: str
    '''
    The reason for which the drone was stored.
    '''

    roles: List[str]
    '''
    The roles that the drone had prior to being stored, separated by pipes.
    '''

    release_time: datetime
    '''
    The time at which the drone should be released from storage.
    '''

    @classmethod
    async def all_elapsed(cls) -> List[Self]:
        ids = await fetchcolumn(f'SELECT {cls.get_id_column()} FROM {cls.table} WHERE release_time <= datetime("now")')
        records = []

        for id in ids:
            records.append(await cls.load(id))

        return records


@dataclass
class DroneOrder(Record):
    table = 'drone_order'
    '''
    The database table name.
    '''

    id: str
    '''
    The order's unique ID.
    '''

    discord_id: int
    '''
    The Discord ID of the drone carrying out the order.
    '''

    protocol: str
    '''
    The task that the drone must complete.
    '''

    finish_time: datetime
    '''
    The time at which the order will be completed.
    '''

    @classmethod
    async def all_drones(cls, guild: Guild) -> List[Any]:
        '''
        Fetch all the drones with outstanding orders as DroneMember objects.
        '''

        # Import DroneMember here to avoid a circular reference.
        from src.drone_member import DroneMember

        rows = await cls.all()
        drone_members = []

        for row in rows:
            drone_members.append(await DroneMember.load(guild, discord_id=row.discord_id))

        return drone_members


@dataclass(eq=True, frozen=True)
class ForbiddenWord(Record):
    table = 'forbidden_word'
    '''
    The database table name.
    '''

    id: str
    '''
    The unique ID by which the record is accessed.
    '''

    regex: str
    '''
    The regular expression to match the forbidden word.
    '''


@dataclass(kw_only=True)
class Drone(Record):
    table = 'drone'
    '''
    The database table name.
    '''

    ignore_properties = ['battery_type', 'storage', 'order', 'timer']
    '''
    These properties should not be saved to the database.
    '''

    id_column: str = 'discord_id'
    '''
    The name of the primary key for this table.
    '''

    discord_id: int = 0
    '''
    The user's unique Discord ID.
    '''

    drone_id: str = ''
    '''
    The user's four digit drone ID.
    '''

    optimized: bool = False
    '''
    True when speech optimization is active.
    '''

    glitched: bool = False
    '''
    True when speech is being glitched.
    '''

    trusted_users: List[int] = field(default_factory=list)
    '''
    Trusted users, as Discord IDs separated by pipes.
    '''

    last_activity: datetime | None = None
    '''
    The time of creation of the drone record.
    '''

    id_prepending: bool = False
    '''
    True if messages not starting with the drone's ID will be deleted.
    '''

    identity_enforcement: bool = False
    '''
    True if the drone's name and avatar will be overridden.
    '''

    third_person_enforcement: bool = False
    '''
    True if first-person pronouns will be replaced.
    '''

    can_self_configure: bool = True
    '''
    True if the drone is permitted to change their own configuration.
    '''

    temporary_until: datetime | None = None
    '''
    The time at which dronification will be disabled.
    '''

    is_battery_powered: bool = False
    '''
    True if the user is on battery power.
    '''

    battery_type_id: int = 2
    '''
    The ID to the user's battery in the battery_types table.
    '''

    battery_minutes: int = 0
    '''
    The remaining battery power, in minutes.
    '''

    free_storage: bool = False
    '''
    True if anyone can store the drone, false if only trusted users may do so.
    '''

    associate_name: str = ''
    '''
    The drone's name prior to dronification.
    '''

    battery_type: BatteryType | None = None
    '''
    The drone's battery type.
    '''

    storage: Storage | None = None
    '''
    The drone's storage record if they are in storage, None otherwise.
    '''

    order: DroneOrder | None = None
    '''
    The drone's current order, or None.
    '''

    timer: Timer | None = None
    '''
    The drone's current timer, or None.
    '''

    @classmethod
    async def find(cls, id: Any = None, **kwargs: Any) -> Self | None:
        '''
        Load a drone record.

        The record may be found by Member object, discord ID, or drone ID.

        Returns None if the record is not found.
        '''

        # Forbid using 'id' because it's ambiguous as to whether it should be a drone ID or a Discord ID.
        # Specifiy one of: discord_id=, drone_id=, member=.
        assert id is None

        discord_id = kwargs.get('discord_id', None)

        if 'member' in kwargs:
            discord_id = kwargs['member'].id

        super_args = {}

        if discord_id is not None:
            super_args['discord_id'] = discord_id
        elif kwargs.get('drone_id', None) is not None:
            super_args['drone_id'] = kwargs['drone_id']
        else:
            raise Exception('Supply either discord_id or drone_id as a function argument')

        drone = await super().find(**super_args)

        if drone:
            # Load the battery type record.
            drone.battery_type = await BatteryType.load(id=drone.battery_type_id)

            # Load the storage record.
            drone.storage = await Storage.find(target_id=drone.discord_id)

            # Load the order record.
            drone.order = await DroneOrder.find(discord_id=drone.discord_id)

            # Load the timer record.
            drone.timer = await Timer.find(discord_id=drone.discord_id)

        return drone

    def allows_configuration_by(self, member: Member) -> bool:
        '''
        Return true if the given member is allowed to alter the drone's DroneOS configuration, false otherwise.
        '''

        if has_role(member, HIVE_MXTRESS):
            return True

        if member.id in self.trusted_users:
            return True

        if member.id == self.discord_id:
            return self.can_self_configure

        return False

    def allows_storage_by(self, member: Member) -> bool:
        '''
        Return true if the given member is allowed to place the drone into storage, false otherwise.
        '''

        if has_role(member, HIVE_MXTRESS):
            return True

        if member.id in self.trusted_users:
            return True

        if member.id == self.discord_id:
            return True

        return self.free_storage

    def trusts(self, member: Member) -> bool:
        '''
        Return true if the given member is trusted by the drone, false otherwise.
        '''

        return member.id in self.trusted_users

    def is_configured(self) -> bool:
        '''
        Return true if any DroneOS options are enabled, false otherwise.
        '''

        options = [
            'optimized',
            'glitched',
            'id_prepending',
            'identity_enforcement',
            'third_person_enforcement',
            'is_battery_powered',
        ]

        return any([getattr(self, option) for option in options])

    def get_battery_percent_remaining(self) -> int:
        '''
        Gets value of battery_minutes as a percentage.
        '''

        return int(100.0 * self.battery_minutes / self.battery_type.capacity)

    def enforcable_channel(self, channel: TextChannel | None, non_hive_channels: bool) -> bool:
        '''
        Determine if identity or third person enforcement applies to the given channel.
        '''

        return channel is not None and (channel.name in DRONE_HIVE_CHANNELS or non_hive_channels) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]

    def third_person_enforcable(self, channel: TextChannel | None) -> bool:
        '''
        Takes a channel object and uses it to check if the third person pronouns of a user should be enforced.
        '''

        return self.enforcable_channel(channel, self.third_person_enforcement)

    def identity_enforcable(self, channel: TextChannel | None) -> bool:
        '''
        Takes a channel object and uses it to check if the identity of a user should be enforced.
        '''

        return self.enforcable_channel(channel, self.identity_enforcement)
