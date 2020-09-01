import logging
from discord.utils import get

from channels import OFFICE
from roles import HIVE_MXTRESS, DRONE, GLITCHED, STORED, ASSOCIATE, has_role

from db.drone_dao import rename_drone_in_db, fetch_drone_with_drone_id, delete_drone_by_drone_id
from db.drone_order_dao import delete_drone_order_by_drone_id
from db.storage_dao import delete_storage_by_target_id

LOGGER = logging.getLogger('ai')


async def rename_drone(context, old_id, new_id):
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


async def unassign_drone(context, drone_id):

    if has_role(context.author, HIVE_MXTRESS) is False or context.channel.name != OFFICE:
        return

    drone = fetch_drone_with_drone_id(drone_id)
    # check for existence
    if drone is None:
        await context.send(f"There is no drone with the ID {drone_id} in the DB.")
        return

    member = context.guild.get_member(drone.id)
    await member.edit(nick=None)
    await member.remove_roles(get(context.guild.roles, name=DRONE), get(context.guild.roles, name=GLITCHED), get(context.guild.roles, name=STORED))
    await member.add_roles(get(context.guild.roles, name=ASSOCIATE))

    # remove from DB
    remove_drone_from_db(drone_id)
    await context.send(f"Drone with ID {drone_id} unassigned.")


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    delete_drone_order_by_drone_id(drone_id)
    delete_storage_by_target_id(drone_id)
    delete_drone_by_drone_id(drone_id)
