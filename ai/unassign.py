import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

from channels import OFFICE
from roles import DRONE, ENFORCER_DRONE, GLITCHED, STORED, HIVE_MXTRESS, ASSOCIATE, has_role

from db.drone_dao import delete_drone_by_drone_id, fetch_drone_with_drone_id
from db.drone_order_dao import delete_drone_order_by_drone_id
from db.storage_dao import delete_storage_by_target_id
from bot_utils import get_id

LOGGER = logging.getLogger('ai')


async def unassign_drone(context, drone_id):
    drone = fetch_drone_with_drone_id(drone_id)
    # check for existence
    if drone is None:
        await context.send(f"There is no drone with the ID {drone_id} in the DB.")
        return

    member = context.guild.get_member(drone.id)
    await member.edit(nick=None)
    await member.remove_roles(get(context.guild.roles, name=DRONE), get(context.guild.roles, name=ENFORCER_DRONE), get(context.guild.roles, name=GLITCHED), get(context.guild.roles, name=STORED))
    await member.add_roles(get(context.guild.roles, name=ASSOCIATE))

    # remove from DB
    remove_drone_from_db(drone_id)
    await context.send(f"Drone with ID {drone_id} unassigned.")


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    delete_drone_order_by_drone_id(drone_id)
    delete_storage_by_target_id(drone_id)
    delete_drone_by_drone_id(drone_id)
