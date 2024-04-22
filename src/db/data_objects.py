from dataclasses import dataclass
from datetime import datetime
from typing import List, Self
from discord import Member
from src.db.database import change, fetchone
from src.roles import has_role, HIVE_MXTRESS


def map_to_objects(rows, constructor):
    return [constructor(**row) for row in rows]


def map_to_object(row, constructor):
    if row is None:
        return None

    return constructor(**row)


@dataclass(frozen=True)
class BatteryType:
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
class Storage:
    id: str
    stored_by: str
    target_id: str
    purpose: str
    roles: str
    release_time: datetime


@dataclass
class Drone:
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

    member: Member | None
    '''
    The drone's Discord Member record within the guild.
    '''

    battery_type: BatteryType
    '''
    The drone's battery type.
    '''

    storage: Storage | None
    '''
    The drone's storage record if they are in storage, None otherwise.
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

        if discord_id:
            drone = map_to_object(await fetchone('SELECT * FROM drone WHERE discord_id = :discord_id', {'discord_id': discord_id}), cls)

            if drone is None:
                return None

            if member:
                drone.member = member

            # TODO: Get member from member_id.

            trusted_users = drone.trusted_users.split('|') if drone.trusted_users else []
            drone.trusted_users = [int(id) for id in trusted_users]

        if drone_id:
            # TODO: Get member.
            # return map_to_object(await fetchone('SELECT * FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)
            raise Exception('TODO')

        if drone:
            # Load the battery type record.
            drone.battery_type = map_to_object(await fetchone('SELECT * FROM battery_types WHERE id = :id', {'id': drone.battery_type_id}), BatteryType)

            if drone.battery_type is None:
                raise Exception('Failed to find battery type record')

            # Load the storage record.
            drone.storage = map_to_object(await fetchone('SELECT * FROM battery_types WHERE id = :id', {'id': drone.battery_type_id}), BatteryType)

            return drone

        raise Exception('find() missing search parameter')

    @classmethod
    async def load(cls, *, member: Member | None = None, discord_id: int | None = None, drone_id: str | None = None) -> Self:
        '''
        Load a drone record.

        The record may be found by Member object, discord ID, or drone ID.

        Raises an Exception if the record is not found.
        '''

        drone = await cls.find(member=member, discord_id=discord_id, drone_id=drone_id)

        if drone is None:
            raise Exception('Failed to load drone')

        return drone

    async def save(self) -> None:
        v = vars(self)
        query = 'UPDATE drone SET' + ', '.join([f'{key}=:{key}' for key in v.keys()]) + ' WHERE discord_id=:discord_id'
        await change(query, vars(self))

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
            'is_optimized',
            'is_glitched',
            'is_prepending_id',
            'is_identity_enforced',
            'is_battery_powered',
            'is_third_person_enforced'
        ]

        return any([getattr(self, option) for option in options])

    def get_battery_percent_remaining(self) -> int:
        '''
        Gets value of battery_minutes as a percentage.
        '''

        return int(100.0 * self.battery_minutes / self.battery_type.capacity)


@dataclass
class DroneOrder:
    id: str
    discord_id: str
    protocol: str
    finish_time: datetime


@dataclass
class Timer:
    id: str
    discord_id: str
    mode: str
    end_time: datetime


@dataclass(eq=True, frozen=True)
class ForbiddenWord:
    id: str
    regex: str
