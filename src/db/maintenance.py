from typing import List
from discord import Member
from src.db.drone_dao import get_all_drones, add_new_drone_members, parse_trusted_users_text, set_trusted_users
from src.db.database import connect
from src.log import log


@connect()
async def sync_drones(members: List[Member]):
    '''
    Add any drones from the guild that are not currently in the database. This mostly exists as convenience in the dev environment.
    '''
    await add_new_drone_members(members)


@connect()
async def trusted_user_cleanup(members: List[Member]):
    '''
    Removes any trusted users that are not members of the guild any more.
    '''
    members_ids = [m.id for m in members]
    drones = await get_all_drones()

    for drone in drones:
        trusted_users = parse_trusted_users_text(drone.trusted_users)
        trimmed_trusted_users = trusted_users.copy()

        for trusted_user in trusted_users:
            if trusted_user not in members_ids:
                log.debug(f'Trusted user with ID {trusted_user} not in the guild anymore; removing')
                trimmed_trusted_users.remove(trusted_user)

        # only do a DB change if something actually changed
        if not trimmed_trusted_users == trusted_users:
            log.debug(f'Trimming {len(trusted_users) - len(trimmed_trusted_users)} trusted users from drone {drone.drone_id}')
            await set_trusted_users(drone.discord_id, trimmed_trusted_users)
