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
    id: str = None
    drone_id: str = None
    optimized: bool = None
    glitched: bool = None
    trusted_users: str = None
    last_activity: datetime = None
    id_prepending: bool = None
    identity_enforcement: bool = None


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
    drone_id: str = None
    protocol: str = None
    finish_time: datetime = None


@dataclass
class Timer:
    id: str = None
    drone_id: str = None
    mode: str = None
    end_time: datetime = None
