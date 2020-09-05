from datetime import datetime
import logging

LOGGER = logging.getLogger("ai")


def map_to_objects(rows, constructor):
    return [constructor(**row) for row in rows]


def map_to_object(row, constructor):
    if row is None:
        return None

    return constructor(**row)


class Drone:

    def __init__(
        self,
        id: str = None,
        drone_id: str = None,
        optimized: bool = None,
        glitched: bool = None,
        trusted_users: str = None,
        last_activity: datetime = None,
        id_prepending: bool = None
    ):
        self.id = id
        self.drone_id = drone_id
        self.optimized = optimized
        self.glitched = glitched
        self.trusted_users = trusted_users
        self.last_activity = last_activity
        self.id_prepending = id_prepending


class Storage:

    def __init__(self, id: str, stored_by: str, target_id: str, purpose: str, roles: str, release_time: datetime):
        self.id = id
        self.stored_by = stored_by
        self.target_id = target_id
        self.purpose = purpose
        self.roles = roles
        self.release_time = release_time


class DroneOrder:

    def __init__(self, id: str = None, drone_id: str = None, protocol: str = None, finish_time: datetime = None):
        self.id = id
        self.drone_id = drone_id
        self.protocol = protocol
        self.finish_time = finish_time
