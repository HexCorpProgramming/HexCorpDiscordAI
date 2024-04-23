from dataclasses import dataclass
from datetime import datetime
from typing import List, Self
from discord import Guild, Member, TextChannel
from src.db.database import change, fetchcolumn, fetchone
from src.channels import DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.roles import has_role, HIVE_MXTRESS
from src.drone_member import DroneMember


def map_to_objects(rows, constructor):
    return [constructor(**row) for row in rows]


def map_to_object(row, constructor):
    if row is None:
        return None

    return constructor(**row)


class Record:
    '''
    The base class for database records.
    This adds the methods: all, find, load, save, insert, delete.
    '''

    @classmethod
    def get_id_column(cls) -> str:
        '''
        Get the name of the column that stores the primary key.

        This will read the `id_column` property if it exists, else it will default to "id".
        '''

        return getattr(cls, 'id_column', 'id')

    def get_id(self) -> str:
        '''
        Get the value of the primary key for this record.
        '''

        return getattr(self, self.get_id_column())

    async def delete(self) -> None:
        '''
        Delete the current database record.
        '''

        await change(f'DELETE FROM {self.table} WHERE {self.get_id_column()} = :id', {'id': self.get_id()})

    @classmethod
    async def find(cls, **kwargs) -> Self | None:
        '''
        Find a database record by the given column name and value.

        Note that the column name is used directly in the SQL and so must not contain user input.
        '''

        if len(kwargs) != 1:
            raise Exception('Record::find() requires exactly one keyword argument')

        column = next(iter(kwargs))
        value = kwargs[column]

        return map_to_object(await fetchone(f'SELECT * FROM {cls.table} WHERE {column} = :value', {'value': value}), cls)

    @classmethod
    async def load(cls, **kwargs) -> Self:
        '''
        Load a single database record.

        Specify a single keyword argument that consists of the column name and value to find.

        Raises an Exception if the record is not found.
        '''

        result = cls.find(**kwargs)

        if result is None:
            column = next(iter(kwargs))
            value = kwargs[column]

            raise Exception(f'Failed to find record in {cls.table_name} where {column} = {value}')

        return result

    @classmethod
    async def all(cls) -> List[Self]:
        '''
        Fetch all records.

        Records are loaded individually in case the class is overriding the load or find method.
        '''

        ids = await fetchcolumn(f'SELECT {cls.get_id_column()} FROM {cls.table}')
        records = []

        for id in ids:
            args = {cls.get_id_column(): id}
            records.append(cls.load(**args))

        return records

    def build_sets(self) -> None:
        '''
        Build a string of "column = :column" for INSERT and UPDATE statements.
        '''

        columns = vars(self).keys()
        ignore_properties = getattr(self, 'ignore_properties', [])

        # Build a string of "col_1 = :col_1, col_2 = :col2" etc.
        return ', '.join([f'{col} = :{col}' for col in columns if col not in ignore_properties])

    async def insert(self) -> None:
        '''
        Insert a new record.
        '''

        sets = self.build_sets()

        await change(f'INSERT INTO {self.table} SET {sets}', vars(self))

    async def save(self) -> None:
        '''
        Update an existing record.
        '''

        sets = self.build_sets()
        id = self.get_id_column()

        await change(f'UPDATE {self.table} SET {sets} WHERE {id} = :{id}', vars(self))


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

    stored_by: str
    '''
    The Discord ID of the user that initiated the storage.
    '''

    target_id: str
    '''
    The Discord ID of the drone that was stored.
    '''

    purpose: str
    '''
    The reason for which the drone was stored.
    '''

    roles: str
    '''
    The roles that the drone had prior to being stored, separated by pipes.
    '''

    release_time: datetime
    '''
    The time at which the drone should be released from storage.
    '''


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

    discord_id: str
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
    async def all_drones(cls, guild: Guild) -> List[DroneMember]:
        '''
        Fetch all drones with an order in progress.
        '''

        drones = []
        ids = await fetchcolumn('SELECT discord_id FROM drone_orders')

        for id in ids:
            drones.append(DroneMember.load(guild, discord_id=id))

        return drones

    @classmethod
    async def all_elapsed(cls, guild: Guild) -> List[DroneMember]:
        '''
        Fetch all drones that are due to be released from storage.
        '''

        drones = []
        ids = await fetchcolumn('SELECT discord_id FROM drone_orders WHERE release_time < :now', {'now': datetime.now()})

        for id in ids:
            drones.append(DroneMember.load(guild, discord_id=id))

        return drones


@dataclass
class Timer(Record):
    table = 'timer'
    '''
    The database table name.
    '''

    id: str
    '''
    The timer's unique ID.
    '''

    discord_id: str
    '''
    The Discord ID of the user to which the timer applies.
    '''

    mode: str
    '''
    The DroneOS parameter being timed.
    '''

    end_time: datetime
    '''
    The time at which the timer expires.
    '''

    @classmethod
    async def all_elapsed(cls, guild: Guild) -> List[DroneMember]:
        '''
        Fetch all drones with elapsed timers.
        '''

        drones = []
        ids = await fetchcolumn('SELECT discord_id FROM timers WHERE end_time < :now', {'now': datetime.now()})

        for id in ids:
            drones.append(DroneMember.load(guild, discord_id=id))

        return drones


@dataclass(eq=True, frozen=True)
class ForbiddenWord:
    id: str
    regex: str


@dataclass
class Drone(Record):
    table = 'drone'
    '''
    The database table name.
    '''

    ignore_properties = ['battery_type', 'storage', 'order']
    '''
    These properties should not be saved to the database.
    '''

    id_column = 'discord_id'
    '''
    The name of the primary key for this table.
    '''

    discord_id: str
    '''
    The user's unique Discord ID.
    '''

    drone_id: str
    '''
    The user's four digit drone ID.
    '''

    optimized: bool
    '''
    True when speech optimization is active.
    '''

    glitched: bool
    '''
    True when speech is being glitched.
    '''

    trusted_users: str | List[int]
    '''
    Trusted users, as Discord IDs separated by pipes.
    '''

    last_activity: datetime | None
    '''
    The time of creation of the drone record.
    '''

    id_prepending: bool
    '''
    True if messages not starting with the drone's ID will be deleted.
    '''

    identity_enforcement: bool
    '''
    True if the drone's name and avatar will be overridden.
    '''

    third_person_enforcement: bool
    '''
    True if first-person pronouns will be replaced.
    '''

    can_self_configure: bool
    '''
    True if the drone is permitted to change their own configuration.
    '''

    temporary_until: datetime | None
    '''
    The time at which dronification will be disabled.
    '''

    is_battery_powered: bool
    '''
    True if the user is on battery power.
    '''

    battery_type_id: int
    '''
    The ID to the user's battery in the battery_types table.
    '''

    battery_minutes: int
    '''
    The remaining battery power, in minutes.
    '''

    free_storage: bool
    '''
    True if anyone can store the drone, false if only trusted users may do so.
    '''

    associate_name: str
    '''
    The drone's name prior to dronification.
    '''

    battery_type: BatteryType
    '''
    The drone's battery type.
    '''

    storage: Storage | None
    '''
    The drone's storage record if they are in storage, None otherwise.
    '''

    order: DroneOrder | None
    '''
    The drone's current order, or None.
    '''

    @classmethod
    async def find(cls, *, member: Member | None = None, discord_id: int | None = None, drone_id: str | None = None) -> Self | None:
        '''
        Load a drone record.

        The record may be found by Member object, discord ID, or drone ID.

        Returns None if the record is not found.
        '''

        if member:
            discord_id = member.id

        drone = await super().find(discord_id=discord_id, drone_id=drone_id)

        if drone:
            # Parse trusted users.
            trusted_users = drone.trusted_users.split('|') if drone.trusted_users else []
            drone.trusted_users = [int(id) for id in trusted_users]

            # Load the battery type record.
            drone.battery_type = await BatteryType.load(id=drone.battery_type_id)

            # Load the storage record.
            drone.storage = await Storage.find(discord_id=drone.discord_id)

            # Load the order record.
            drone.order = await DroneOrder.find(discord_id=drone.discord_id)

        return drone

    async def save(self) -> None:
        '''
        Save the record to the database.

        Serializes the trusted users before saving.
        '''

        temp = self.trusted_users
        self.trusted_users = '|'.join(self.trusted_users)
        await super().save()
        self.trusted_users = temp

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
            'identity_enforced',
            'third_person_enforced'
            'is_battery_powered',
        ]

        return any([getattr(self, option) for option in options])

    def get_battery_percent_remaining(self) -> int:
        '''
        Gets value of battery_minutes as a percentage.
        '''

        return int(100.0 * self.battery_minutes / self.battery_type.capacity)

    def third_person_enforcable(self, channel: TextChannel) -> bool:
        '''
        Takes a context or channel object and uses it to check if the identity of a user should be enforced.
        '''

        return (channel.name in DRONE_HIVE_CHANNELS or self.third_person_enforced) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]
