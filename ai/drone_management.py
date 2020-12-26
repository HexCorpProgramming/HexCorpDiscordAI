import logging
from discord.utils import get

from roles import DRONE, GLITCHED, STORED, ASSOCIATE, ID_PREPENDING, IDENTITY_ENFORCEMENT, SPEECH_OPTIMIZATION
from id_converter import convert_id_to_member
from display_names import update_display_name

from db.drone_dao import rename_drone_in_db, fetch_drone_with_drone_id, delete_drone_by_drone_id, fetch_drone_with_id, update_droneOS_parameter
from db.drone_order_dao import delete_drone_order_by_drone_id
from db.storage_dao import delete_storage_by_target_id
from db.timer_dao import delete_timers_by_drone_id

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
    delete_timers_by_drone_id(drone_id)


async def emergency_release(context, drone_id: str):
    drone_member = convert_id_to_member(context.guild, drone_id)

    if drone_member is None:
        await context.channel.send(f"No drone with ID {drone_id} found.")
        return

    update_droneOS_parameter(drone_member, "id_prepending", False)
    update_droneOS_parameter(drone_member, "optimized", False)
    update_droneOS_parameter(drone_member, "identity_enforcement", False)
    update_droneOS_parameter(drone_member, "glitched", False)
    await drone_member.remove_roles(get(context.guild.roles, name=SPEECH_OPTIMIZATION), get(context.guild.roles, name=GLITCHED), get(context.guild.roles, name=ID_PREPENDING), get(context.guild.roles, name=IDENTITY_ENFORCEMENT))
    await update_display_name(drone_member)

    await context.channel.send(f"Restrictions disabled for drone {drone_id}.")
