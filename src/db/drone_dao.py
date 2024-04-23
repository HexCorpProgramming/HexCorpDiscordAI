from datetime import datetime
from typing import List

import discord

from src.db.data_objects import Drone, map_to_objects
from src.db.database import fetchall, fetchone, fetchcolumn
from src.bot_utils import get_id
from src.roles import DRONE, STORED, has_any_role


async def add_new_drone_members(members: List[discord.Member]):
    '''
    Adds the given list of Members as drone entities to the DB if they are not already present.
    '''
    for member in members:
        if has_any_role(member, [DRONE, STORED]):

            if await fetchone("SELECT 1 FROM drone WHERE discord_id=:id", {"id": member.id}) is None:
                drone_id = get_id(member.display_name)

                if drone_id:
                    new_drone = Drone(member.id, drone_id, False, False, '', datetime.now(), associate_name=member.display_name)
                    await new_drone.insert()


async def get_used_drone_ids() -> List[str]:
    '''
    Returns all IDs currently used by drones.
    '''

    return await fetchcolumn('SELECT drone_id FROM drone')


async def fetch_all_elapsed_temporary_dronification() -> List[Drone]:
    '''
    Finds all drones, whose temporary dronification timer is up.
    '''
    return map_to_objects(await fetchall('SELECT * FROM drone WHERE temporary_until < :now', {'now': datetime.now()}), Drone)


async def remove_trusted_user_on_all(trusted_user_id: int):
    '''
    Removes the trusted user with the given discord ID from all trusted_users lists of all drones.
    '''

    ids = await fetchcolumn("SELECT discord_id FROM drone WHERE trusted_users LIKE :trusted_user_search", {'trusted_user_search': f"%{trusted_user_id}%"})

    for id in ids:
        drone = Drone.load(discord_id=id)

        if trusted_user_id in drone.trusted_users:
            drone.trusted_users.remove(trusted_user_id)

        await drone.save()
