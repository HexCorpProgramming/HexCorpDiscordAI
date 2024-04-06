from dataclasses import dataclass
from datetime import datetime
import logging

LOGGER = logging.getLogger("ai")


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
    temporary_until: datetime = None
    battery_minutes: int = None
    is_battery_powered: bool = None
    can_self_configure: bool = None
    associate_name: str = None
    free_storage: bool = None


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
