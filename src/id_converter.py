import re
from typing import Optional, Set

import discord

from src.db.drone_dao import get_discord_id_of_drone


async def convert_ids_to_members(guild: discord.Guild, drone_ids) -> Set[discord.Member]:
    '''
    Takes a list of string IDs (e.g "5890", "9813") and returns a list of converted member objects.
    '''

    drone_members = set()

    for drone_id in drone_ids:
        drone_member = await convert_id_to_member(guild, drone_id)
        if drone_member is not None:
            drone_members.add(drone_member)

    return drone_members


async def convert_id_to_member(guild: discord.Guild, drone_id: str) -> Optional[discord.Member]:
    '''
    Takes a given drone ID (e.g "5890") and returns it as a member object if available.
    '''

    if not re.match(r"^\d{4}$", drone_id):
        return None  # Can't match something that isn't a drone ID.

    if (drone_from_db := await get_discord_id_of_drone(drone_id)) is None:
        return None  # Drone not present in DB.

    drone_member = guild.get_member(drone_from_db)
    if drone_member is None:
        return None  # Drone was present in DB, but is somehow not present in server.

    return drone_member
