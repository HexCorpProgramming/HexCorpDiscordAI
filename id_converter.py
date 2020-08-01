import discord
import re
from db.drone_dao import get_discord_id_of_drone
from typing import List, Optional


def convert_ids_to_members(guild: discord.Guild, drone_ids) -> List[discord.Member]:
    '''
    Takes a list of string IDs (e.g "5890", "9813") and returns a list of converted member objects.
    '''

    drone_members = []

    for drone_id in drone_ids:
        drone_member = convert_id_to_member(guild, drone_id)
        print("Drone member is:")
        print(drone_member)
        if drone_member is not None:
            drone_members.append(drone_member)

    return drone_members


def convert_id_to_member(guild: discord.Guild, drone_id) -> Optional[discord.Member]:
    '''
    Takes a given drone ID (e.g "5890") and returns it as a member object if available.
    '''

    if not re.match(r"^\d{4}$", drone_id):
        return None  # Can't match something that isn't a drone ID.

    if (drone_from_db := get_discord_id_of_drone(drone_id)) is None:
        return None  # Drone not present in DB.

    drone_member = guild.get_member(drone_from_db.id)
    if drone_member is None:
        return None  # Drone was present in DB, but is somehow not present in server.

    return drone_member
