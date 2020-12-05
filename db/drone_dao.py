import discord
from typing import List

from db.database import fetchone, change, fetchall

from roles import DRONE, STORED, has_any_role
from bot_utils import get_id
from datetime import datetime
from db.data_objects import Drone, map_to_object
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
    change('INSERT INTO drone(id, drone_id, optimized, glitched, trusted_users, last_activity) VALUES (:id, :drone_id, :optimized, :glitched, :trusted_users, :last_activity)', vars(drone))


def fetch_drone_with_drone_id(drone_id: str) -> Drone:
    '''
    Finds a drone with the given drone_id.
    '''
    return map_to_object(fetchone('SELECT id, drone_id, optimized, glitched, id_prepending, trusted_users, last_activity FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)


def fetch_drone_with_id(discord_id: int) -> Drone:
    '''
    Finds a drone with the given discord_id.
    '''
    return map_to_object(fetchone('SELECT id, drone_id, optimized, glitched, trusted_users, last_activity FROM drone WHERE id = :discord_id', {'discord_id': discord_id}), Drone)


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


def get_discord_id_of_drone(drone_id: str) -> str:
    '''
    Returns the discord ID associated with a given drone
    '''
    # TODO: needs to be reworked; does not do what it says on the tin
    return map_to_object(fetchone('SELECT id FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)


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
    drone = fetchone('SELECT id FROM drone WHERE id = :discord', {'discord': member.id})
    return drone is not None


def is_optimized(drone: discord.Member) -> bool:
    optimized_drone = fetchone('SELECT optimized FROM drone WHERE id = :discord', {'discord': drone.id})
    return optimized_drone is not None and bool(optimized_drone['optimized'])


def is_glitched(drone: discord.Member) -> bool:
    glitched_drone = fetchone('SELECT glitched FROM drone WHERE id = :discord', {'discord': drone.id})
    return glitched_drone is not None and bool(glitched_drone['glitched'])


def is_prepending_id(drone: discord.Member) -> bool:
    prepending_drone = fetchone('SELECT id_prepending FROM drone WHERE id = :discord', {'discord': drone.id})
    return prepending_drone is not None and bool(prepending_drone['id_prepending'])


def is_identity_enforced(drone: discord.Member) -> bool:
    enforced_drone = fetchone('SELECT identity_inforcement FROM drone WHERE id = :discord', {'discord': drone.id})
    return enforced_drone is not None and bool(enforced_drone['identity_inforcement'])


def get_trusted_users(discord_id: int) -> List[int]:
    trusted_users_text = fetchone('SELECT trusted_users FROM drone WHERE id = :discord', {'discord': discord_id})['trusted_users']
    if not trusted_users_text:
        return []
    else:
        return [int(user) for user in trusted_users_text.split("|")]


def set_trusted_users(discord_id: int, trusted_users: List[int]):
    trusted_users_text = "|".join([str(trusted_user) for trusted_user in trusted_users])
    change("UPDATE drone SET trusted_users = :trusted_users_text WHERE id = :discord", {'trusted_users_text': trusted_users_text, 'discord': discord_id})
