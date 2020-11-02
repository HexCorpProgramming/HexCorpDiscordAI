import logging
from discord.utils import get

from roles import DRONE, GLITCHED, STORED, ASSOCIATE

from db.drone_dao import rename_drone_in_db, fetch_drone_with_drone_id, delete_drone_by_drone_id, fetch_drone_with_id
from db.drone_order_dao import delete_drone_order_by_drone_id
from db.storage_dao import delete_storage_by_target_id

LOGGER = logging.getLogger('ai')


async def rename_drone(context, old_id: str, new_id: str):
    if len(old_id) != 4 or len(new_id) != 4:
        return
    if not old_id.isnumeric() or not new_id.isnumeric():
        return

    LOGGER.info("IDs to rename drone to and from are both valid.")

    # check for collisions
    collision = fetch_drone_with_drone_id(new_id)
    if collision is None:
        drone = fetch_drone_with_drone_id(old_id)
        member = context.guild.get_member(drone.id)
        rename_drone_in_db(old_id, new_id)
        await member.edit(nick=f'⬡-Drone #{new_id}')
        await context.send(f"Successfully renamed drone {old_id} to {new_id}.")
    else:
        await context.send(f"ID {new_id} already in use.")


async def unassign_drone(context):
    drone = fetch_drone_with_id(context.author.id)
    # check for existence
    if drone is None:
        await context.send("You are not a drone. Can not unassign.")
        return

    guild = context.bot.guilds[0]
    member = guild.get_member(context.author.id)
    await member.edit(nick=None)
    await member.remove_roles(get(guild.roles, name=DRONE), get(guild.roles, name=GLITCHED), get(guild.roles, name=STORED))
    await member.add_roles(get(guild.roles, name=ASSOCIATE))

    # remove from DB
    remove_drone_from_db(drone.drone_id)
    await context.send(f"Drone with ID {drone.drone_id} unassigned.")


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    delete_drone_order_by_drone_id(drone_id)
    delete_storage_by_target_id(drone_id)
    delete_drone_by_drone_id(drone_id)
