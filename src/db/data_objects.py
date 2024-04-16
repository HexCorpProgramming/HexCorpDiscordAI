from dataclasses import dataclass
from datetime import datetime


def map_to_objects(rows, constructor):
    return [constructor(**row) for row in rows]


def map_to_object(row, constructor):
    if row is None:
        return None

    return constructor(**row)


@dataclass
class Drone:
    discord_id: str = None
    drone_id: str = None
    optimized: bool = None
    glitched: bool = None
    trusted_users: str = None
    last_activity: datetime = None
    id_prepending: bool = None
    identity_enforcement: bool = None
    can_self_configure: bool = None
    temporary_until: datetime = None
    is_battery_powered: bool = None
    battery_type_id: int = None
    battery_minutes: int = None
    free_storage: bool = None
    associate_name: str = None


@dataclass
class Storage:
    id: str
    stored_by: str
    target_id: str
    purpose: str
    roles: str
    release_time: datetime


@dataclass
class DroneOrder:
    id: str = None
    discord_id: str = None
    protocol: str = None
    finish_time: datetime = None


@dataclass
class Timer:
    id: str = None
    discord_id: str = None
    mode: str = None
    end_time: datetime = None


@dataclass(eq=True, frozen=True)
class ForbiddenWord:
    id: str = None
    regex: str = None


@dataclass(frozen=True)
class BatteryType:
    # The primary key.
    id: int = None
    # The type name, e.g. "Medium"
    name: str = None
    # The battery's duration, in minutes.
    capacity: int = None
    # The battery's recharge rate, in minutes of capacity gained per hour of recharge.
    recharge_rate: int = None
