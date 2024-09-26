from typing import List
from discord import Member
from src.db.drone_dao import add_new_drone_members
from src.db.database import connect
from src.db.data_objects import Drone
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
    member_ids = [m.id for m in members]
    drones = await Drone.all()

    for drone in drones:
        original_count = len(drone.trusted_users)

        drone.trusted_users = [u for u in drone.trusted_users if u in member_ids]

        if len(drone.trusted_users) != original_count:
            log.debug(f'Trimming {original_count - len(drone.trusted_users)} trusted users from drone {drone.drone_id}')
            await drone.save()
