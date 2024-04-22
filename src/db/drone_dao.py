from datetime import datetime
from typing import List, Optional

import discord

from src.db.data_objects import BatteryType, Drone, map_to_object, map_to_objects
from src.db.database import change, fetchall, fetchone, fetchcolumn
from src.resources import HIVE_MXTRESS_USER_ID
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
                    new_drone = Drone(member.id, drone_id, False, False, HIVE_MXTRESS_USER_ID, datetime.now(), associate_name=member.display_name)
                    await insert_drone(new_drone)


async def insert_drone(drone: Drone):
    '''
    Inserts the given drone into the table drone.
    '''
    await change('INSERT INTO drone(discord_id, drone_id, optimized, glitched, trusted_users, last_activity, temporary_until, associate_name) VALUES (:discord_id, :drone_id, :optimized, :glitched, :trusted_users, :last_activity, :temporary_until, :associate_name)', vars(drone))


async def fetch_drone_with_drone_id(drone_id: str) -> Drone | None:
    '''
    Finds a drone with the given drone_id.
    '''
    return map_to_object(await fetchone('SELECT * FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id}), Drone)


async def fetch_drone_with_id(discord_id: int) -> Drone | None:
    '''
    Finds a drone with the given discord_id.
    '''
    return map_to_object(await fetchone('SELECT * FROM drone WHERE discord_id = :discord_id', {'discord_id': discord_id}), Drone)


async def get_all_drones() -> List[Drone]:
    return map_to_objects(await fetchall('SELECT * FROM drone', {}), Drone)


async def get_all_drone_batteries() -> List[Drone]:
    return map_to_objects(await fetchall('SELECT * FROM drone', {}), Drone)


async def rename_drone_in_db(old_id: str, new_id: str):
    '''
    Changes the ID of a drone.
    '''
    await change('UPDATE drone SET drone_id=:new_id WHERE drone_id=:old_id', {'new_id': new_id, 'old_id': old_id})


async def delete_drone_by_drone_id(drone_id: str):
    '''
    Deletes the drone with the given drone_id.
    '''
    await change('DELETE FROM drone WHERE drone_id=:drone_id', {'drone_id': drone_id})


async def get_discord_id_of_drone(drone_id: str) -> Optional[int]:
    '''
    Returns the discord ID associated with a given drone
    '''
    id = await fetchone('SELECT discord_id FROM drone WHERE drone_id = :drone_id', {'drone_id': drone_id})
    return id['discord_id'] if id else None


async def get_used_drone_ids() -> List[str]:
    '''
    Returns all IDs currently used by drones.
    '''

    return await fetchcolumn('SELECT drone_id FROM drone')


async def update_droneOS_parameter(member: discord.Member, column: str, value: bool):
    '''
    Updates DroneOS parameters for the requested drone and parameter.
    '''
    await change(f'UPDATE drone SET {column} = :value WHERE discord_id = :discord', {'value': value, 'discord': member.id})
    # Hive Mxtress forgive me for I hath concatenated in an SQL query.
    # BUT IT'S FINEEEE 'cus the only functions that call this have a preset column value that is never based on user input.


async def is_drone(member: discord.Member) -> bool:
    '''
    Determines if a given member is registered as a drone.
    '''
    drone = await fetchone('SELECT 1 FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return drone is not None


async def is_optimized(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and optimized.
    '''
    optimized_drone = await fetchone('SELECT optimized FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return optimized_drone is not None and bool(optimized_drone['optimized'])


async def is_glitched(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and glitched.
    '''
    glitched_drone = await fetchone('SELECT glitched FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return glitched_drone is not None and bool(glitched_drone['glitched'])


async def is_prepending_id(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and in id prepending mode.
    '''
    prepending_drone = await fetchone('SELECT id_prepending FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return prepending_drone is not None and bool(prepending_drone['id_prepending'])


async def is_identity_enforced(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and identity enforced.
    '''
    enforced_drone = await fetchone('SELECT identity_enforcement FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return enforced_drone is not None and bool(enforced_drone['identity_enforcement'])


async def is_third_person_enforced(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and third-person enforced.
    '''

    enforced_drone = await fetchone('SELECT third_person_enforcement FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return enforced_drone is not None and bool(enforced_drone['third_person_enforcement'])


async def can_self_configure(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and can self-configure its other configs.
    '''
    can_self_configure_drone = await fetchone('SELECT can_self_configure FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return can_self_configure_drone is not None and bool(can_self_configure_drone['can_self_configure'])


async def is_battery_powered(member: discord.Member) -> bool:
    '''
    Determines if the given member is a drone and is on battery power.
    '''
    battery_powered_drone = await fetchone('SELECT is_battery_powered FROM drone WHERE discord_id = :discord', {'discord': member.id})
    return battery_powered_drone is not None and bool(battery_powered_drone['is_battery_powered'])


async def deincrement_battery_minutes_remaining(member: Optional[discord.Member] = None, drone_id: Optional[str] = None):
    '''
    Deincrements value of battery_minutes by the specified amount.
    Raises a ValueError if drone is not found.
    '''
    if member is not None:
        drone_record = await fetchone('SELECT battery_minutes FROM drone WHERE member_id = :discord', {'discord': member.id})
        await change('UPDATE drone SET battery_minutes = :minutes WHERE discord_id = :discord', {'minutes': drone_record['battery_minutes'] - 1, 'discord': member.id})
    elif drone_id is not None:
        drone_record = await fetchone('SELECT battery_minutes FROM drone WHERE drone_id = :drone', {'drone': drone_id})
        await change('UPDATE drone SET battery_minutes = :minutes WHERE drone_id = :drone_id', {'minutes': drone_record['battery_minutes'] - 1, 'drone_id': drone_id})
    else:
        raise ValueError('Could not deincrement drone battery. No Discord member or drone ID provided.')


async def set_battery_minutes_remaining(member: discord.Member, minutes: int):
    '''
    Sets the value of battery_minutes to the specified amount.
    '''

    await change('UPDATE drone SET battery_minutes = :minutes WHERE discord_id = :discord', {'minutes': max(0, minutes), 'discord': member.id})


async def get_battery_minutes_remaining(member: discord.Member) -> int:
    '''
    Gets value of battery_minutes from drone table based on a given drone's Discord ID.
    Raises an Exception if the drone is not found.
    '''

    drone = await fetchone('SELECT battery_minutes FROM drone WHERE discord_id = :discord', {'discord': member.id})

    if drone is None:
        raise Exception('No drone record for member ' + str(member.id))

    return drone['battery_minutes']


async def fetch_all_elapsed_temporary_dronification() -> List[Drone]:
    '''
    Finds all drones, whose temporary dronification timer is up.
    '''
    return map_to_objects(await fetchall('SELECT * FROM drone WHERE temporary_until < :now', {'now': datetime.now()}), Drone)


async def is_free_storage(drone: Drone) -> bool:
    '''
    Determines if the given member is a drone and can be freely stored by anyone.
    '''
    free_storage_drone = await fetchone('SELECT free_storage FROM drone WHERE discord_id = :discord', {'discord': drone.discord_id})
    return free_storage_drone is not None and bool(free_storage_drone['free_storage'])


async def get_battery_types() -> List[BatteryType]:
    '''
    Fetch all the battery types.
    '''

    return map_to_objects(await fetchall('SELECT * FROM battery_types'), BatteryType)


async def set_battery_type(member: discord.Member, type: BatteryType) -> None:
    '''
    Set the battery type for a drone.
    '''

    await change('UPDATE drone SET battery_type_id = :type_id WHERE discord_id = :discord_id', {'type_id': type.id, 'discord_id': member.id})


async def remove_trusted_user_on_all(trusted_user_id: int):
    '''
    Removes the trusted user with the given discord ID from all trusted_users lists of all drones.
    '''

    ids = await fetchcolumn("SELECT discord_id FROM drone WHERE trusted_users LIKE :trusted_user_search", {'trusted_user_search': f"%{trusted_user_id}%"})

    for id in ids:
        drone = Drone.load(discord_id=id)
        drone.trusted_users.remove(trusted_user_id)
        await drone.save()
