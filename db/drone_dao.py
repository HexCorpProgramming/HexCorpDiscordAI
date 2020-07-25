import discord
from typing import List

from db.database import fetchone, change

from roles import DRONE, STORED, has_any_role
from bot_utils import get_id
from datetime import datetime
from db.data_objects import Drone, map_to_object


def add_new_drone_members(members: List[discord.Member]):
    '''
    Adds the given list of Members as drone entities to the DB if they are not already present.
    '''
    for member in members:
        if has_any_role(member, [DRONE, STORED]):

            if fetchone("SELECT id FROM drone WHERE id=:id", {"id": member.id}) is None:
                new_drone = Drone(member.id, get_id(member.display_name), False, False, "", datetime.now())
                insert_drone(new_drone)


def insert_drone(drone: Drone):
    '''
    Inserts the given drone into the table drone.
    '''
    change('INSERT INTO drone VALUES (:id, :drone_id, :optimized, :glitched, :trusted_users, :last_activity)', vars(drone))


def fetch_drone_with_drone_id(drone_id: str) -> Drone:
    '''
    Finds a drone with the given drone_id.
    '''
    return map_to_object(fetchone('SELECT id, drone_id, optimized, glitched, trusted_users, last_activity FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)


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
    return map_to_object(fetchone('SELECT id FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)
