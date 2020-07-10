from datetime import datetime


class Drone:

    def __init__(self, id: int, drone_id: str, optimized: bool, glitched: bool, trusted_users: str, last_activity: datetime):
        self.id = id
        self.drone_id = drone_id
        self.optimized = optimized
        self.glitched = glitched
        self.trusted_users = trusted_users
        self.last_activity = last_activity


class Storage:

    def __init__(self, id: str, stored_by: str, target_id: str, purpose: str, roles: str, release_time: datetime):
        self.id = id
        self.stored_by = stored_by
        self.target_id = target_id
        self.purpose = purpose
        self.roles = roles
        self.release_time = release_time


class DroneOrder:

    def __init__(self, id: str, drone_id: str, protocol: str, finish_time: datetime):
        self.id = id
        self.drone_id = drone_id
        self.protocol = protocol
        self.finish_time = finish_time
