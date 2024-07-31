from datetime import datetime
from typing import List

import discord

from src.db.data_objects import Drone
from src.db.database import change, fetchall, fetchone, fetchcolumn
from src.bot_utils import get_id
from src.roles import DRONE, STORED, has_any_role
from src.drone_member import DroneMember


async def add_new_drone_members(members: List[discord.Member]):
    '''
    Adds the given list of Members as drone entities to the DB if they are not already present.
    '''
    for member in members:
        if has_any_role(member, [DRONE, STORED]):

            if await fetchone("SELECT 1 FROM drone WHERE discord_id=:id", {"id": member.id}) is None:
                drone_id = get_id(member.display_name)

                if drone_id:
                    new_drone = Drone(discord_id=member.id, drone_id=drone_id, last_activity=datetime.now(), associate_name=member.display_name)
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

    return [Drone(**row) for row in await fetchall('SELECT * FROM drone WHERE temporary_until < :now', {'now': datetime.now()})]


async def remove_trusted_user_on_all(trusted_user_id: int):
    '''
    Removes the trusted user with the given discord ID from all trusted_users lists of all drones.
    '''

    ids = await fetchcolumn("SELECT discord_id FROM drone WHERE trusted_users LIKE :trusted_user_search", {'trusted_user_search': f"%{trusted_user_id}%"})

    for id in ids:
        drone = await Drone.load(discord_id=id)

        if trusted_user_id in drone.trusted_users:
            drone.trusted_users.remove(trusted_user_id)
            await drone.save()


async def get_drones_with_orders(guild: discord.Guild) -> List[DroneMember]:
    '''
    Fetch all drones with an order in progress.
    '''

    ids = await fetchcolumn('SELECT discord_id FROM drone_orders')

    return [await DroneMember.load(guild, discord_id=id) for id in ids]


async def get_drones_to_release(guild: discord.Guild) -> List[DroneMember]:
    '''
    Fetch all drones that are due to be released from storage.
    '''

    ids = await fetchcolumn('SELECT discord_id FROM drone_orders WHERE release_time < :now', {'now': datetime.now()})

    return [await DroneMember.load(guild, discord_id=id) for id in ids]


async def get_drones_with_elapsed_timers(guild: discord.Guild) -> List[DroneMember]:
    '''
    Fetch all drones with elapsed timers.
    '''

    ids = await fetchcolumn('SELECT discord_id FROM timers WHERE end_time < :now', {'now': datetime.now()})

    return [await DroneMember.load(guild, discord_id=id) for id in ids]


async def delete_timers_by_id_and_mode(discord_id: str, mode: str):
    '''
    Deletes the timer with the given ID and mode.
    '''

    await change('DELETE FROM timer WHERE discord_id = :discord_id AND timer.mode = :mode', {'discord_id': discord_id, 'mode': mode})
