import discord
from typing import List, Optional

from db.database import fetchone, change, fetchall

from roles import DRONE, STORED, has_any_role
from bot_utils import get_id
from datetime import datetime
from db.data_objects import Drone, map_to_object, map_to_objects
from resources import HIVE_MXTRESS_USER_ID


def add_new_drone_members(members: List[discord.Member]):
    '''
    Adds the given list of Members as drone entities to the DB if they are not already present.
    '''
    for member in members:
        if has_any_role(member, [DRONE, STORED]):

            if fetchone("SELECT id FROM drone WHERE id=:id", {"id": member.id}) is None:
                new_drone = Drone(member.id, get_id(member.display_name), False, False, HIVE_MXTRESS_USER_ID, datetime.now())
                insert_drone(new_drone)


def insert_drone(drone: Drone):
    '''
    Inserts the given drone into the table drone.
    '''
    change('INSERT INTO drone(id, drone_id, optimized, glitched, trusted_users, last_activity, temporary_until) VALUES (:id, :drone_id, :optimized, :glitched, :trusted_users, :last_activity, :temporary_until)', vars(drone))


def fetch_drone_with_drone_id(drone_id: str) -> Drone:
    '''
    Finds a drone with the given drone_id.
    '''
    return map_to_object(fetchone('SELECT id, drone_id, optimized, glitched, id_prepending, identity_enforcement, trusted_users, last_activity, temporary_until FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)


def fetch_drone_with_id(discord_id: int) -> Drone:
    '''
    Finds a drone with the given discord_id.
    '''
    return map_to_object(fetchone('SELECT id, drone_id, optimized, glitched, trusted_users, last_activity, temporary_until FROM drone WHERE id = :discord_id', {'discord_id': discord_id}), Drone)


def rename_drone_in_db(old_id: str, new_id: str):
    '''
    Changes the ID of a drone.
    '''
    change('UPDATE drone SET drone_id=:new_id WHERE drone_id=:old_id', {'new_id': new_id, 'old_id': old_id})


def delete_drone_by_drone_id(drone_id: str):
    '''
    Deletes the drone with the given drone_id.
    '''
    change('DELETE FROM drone WHERE drone_id=:drone_id', {'drone_id': drone_id})


def get_discord_id_of_drone(drone_id: str) -> Optional[int]:
    '''
    Returns the discord ID associated with a given drone
    '''
    id = fetchone('SELECT id FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id})
    return id['id'] if id else None


def get_used_drone_ids() -> List[str]:
    '''
    Returns all IDs currently used by drones.
    '''
    # TODO: unpacking a single column could be extracted into a function
    return [row['drone_id'] for row in fetchall('SELECT drone_id from drone', {})]


def update_droneOS_parameter(drone: discord.Member, column: str, value: bool):
    change(f'UPDATE drone SET {column} = :value WHERE id = :discord', {'value': value, 'discord': drone.id})
    # Hive Mxtress forgive me for I hath concatenated in an SQL query.
    # BUT IT'S FINEEEE 'cus the only functions that call this have a preset column value that is never based on user input.


def is_drone(member: discord.Member) -> bool:
    '''
    Determines if a given member is registered as a drone.
    '''
    drone = fetchone('SELECT id FROM drone WHERE id = :discord', {'discord': member.id})
    return drone is not None


def is_optimized(drone: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and optimized.
    '''
    optimized_drone = fetchone('SELECT optimized FROM drone WHERE id = :discord', {'discord': drone.id})
    return optimized_drone is not None and bool(optimized_drone['optimized'])


def is_glitched(drone: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and glitched.
    '''
    glitched_drone = fetchone('SELECT glitched FROM drone WHERE id = :discord', {'discord': drone.id})
    return glitched_drone is not None and bool(glitched_drone['glitched'])


def is_prepending_id(drone: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and in id prepending mode.
    '''
    prepending_drone = fetchone('SELECT id_prepending FROM drone WHERE id = :discord', {'discord': drone.id})
    return prepending_drone is not None and bool(prepending_drone['id_prepending'])


def is_identity_enforced(drone: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and identity enforced.
    '''
    enforced_drone = fetchone('SELECT identity_enforcement FROM drone WHERE id = :discord', {'discord': drone.id})
    return enforced_drone is not None and bool(enforced_drone['identity_enforcement'])


def can_self_configure(drone: discord.Member) -> bool:
    can_self_configure_drone = fetchone('SELECT can_self_configure FROM drone WHERE id = :discord', {'discord': drone.id})
    return can_self_configure_drone is not None and bool(can_self_configure_drone['can_self_configure'])


def get_trusted_users(discord_id: int) -> List[int]:
    '''
    Finds the list of trusted users for the drone with the given discord ID.
    '''
    trusted_users_text = fetchone('SELECT trusted_users FROM drone WHERE id = :discord', {'discord': discord_id})['trusted_users']
    return parse_trusted_users_text(trusted_users_text)


def parse_trusted_users_text(trusted_users_text: str) -> List[int]:
    '''
    Parses the given list of trusted_users of a drone into a list of discord IDs corresponding to the users.
    '''
    if not trusted_users_text:
        return []
    else:
        return [int(user) for user in trusted_users_text.split("|")]


def set_trusted_users(discord_id: int, trusted_users: List[int]):
    '''
    Sets the trusted_users list of the drone with the given discord ID to the given list.
    '''
    trusted_users_text = "|".join([str(trusted_user) for trusted_user in trusted_users])
    change("UPDATE drone SET trusted_users = :trusted_users_text WHERE id = :discord", {'trusted_users_text': trusted_users_text, 'discord': discord_id})


def fetch_all_elapsed_temporary_dronification() -> List[Drone]:
    '''
    Finds all drones, whose temporary dronification timer is up.
    '''
    return map_to_objects(fetchall('SELECT id, drone_id, optimized, glitched, trusted_users, last_activity, temporary_until FROM drone WHERE temporary_until < :now', {'now': datetime.now()}), Drone)


def fetch_all_drones_with_trusted_user(trusted_user_id: int) -> List[Drone]:
    '''
    Finds all drones, that have the user with the given ID as a trusted user.
    '''
    return map_to_objects(fetchall("SELECT drone.* FROM drone WHERE drone.trusted_users LIKE :trusted_user_search", {'trusted_user_search': f"%{trusted_user_id}%"}))
