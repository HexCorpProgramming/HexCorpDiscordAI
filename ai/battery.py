from bot_utils import get_id
from discord.ext import tasks
from db.drone_dao import is_drone, is_battery_powered, deincrement_battery_minutes_remaining, get_all_drone_batteries
from id_converter import convert_id_to_member
import logging
from resources import MAX_BATTERY_CAPACITY_MINS
from roles import has_role, BATTERY_POWERED, BATTERY_DRAINED
from discord.utils import get

draining_batteries = {}  # {drone_id: minutes of drain left}

LOGGER = logging.getLogger('ai')


async def start_battery_drain(message, message_copy=None):
    '''
    If message author has battery DroneOS config enabled, begin or restart
    the task to drain 1 minute of battery per minute, for 15 minutes.
    '''

    if not is_drone(message.author) or not is_battery_powered(message.author):
        return False

    drone_id = get_id(message.author.display_name)
    draining_batteries[drone_id] = 15


@tasks.loop(minutes=1)
async def track_active_battery_drain(bot):
    LOGGER.info("Draining battery from active drones.")

    inactive_drones = []

    for drone, remaining_minutes in draining_batteries.items():
        if remaining_minutes == 0:
            LOGGER.info(f"Drone {drone} has been idle for 15 minutes. No longer draining power.")
            # Cannot alter list while iterating, so add drone to list of drones to pop after the loop.
            inactive_drones.append(drone)
        else:
            print(f"Draining 1 minute worth of charge from {drone}")
            draining_batteries[drone] = remaining_minutes - 1
            deincrement_battery_minutes_remaining(convert_id_to_member(bot.guilds[0], drone))

    for inactive_drone in inactive_drones:
        LOGGER.info(f"Removing {inactive_drone} from drain list.")
        draining_batteries.pop(inactive_drone)


@tasks.loop(minutes=1)
async def track_drained_batteries(bot):
    # Every drone has a battery. If battery_minutes = 0, give the Drained role.
    # If battery_minutes > 0 and it has the Drained role, remove it.
    for drone in get_all_drone_batteries():
        # Intentionally different math to that in DAO b/c it always rounds down.
        member_drone = bot.guilds[0].get_member(drone.id)
        if member_drone is None:
            LOGGER.warn(f"Drone {drone.drone_id} not found in server but present in database.")
            continue
        if (drone.battery_minutes / MAX_BATTERY_CAPACITY_MINS * 100) == 0 and has_role(member_drone, BATTERY_POWERED):
            LOGGER.debug(f"Drone {drone.drone_id} is out of battery.")
            await member_drone.add_roles(get(bot.guilds[0].roles, name=BATTERY_DRAINED))
        elif (drone.battery_minutes / MAX_BATTERY_CAPACITY_MINS * 100) != 0 and has_role(member_drone, BATTERY_DRAINED):
            LOGGER.debug(f"Drone {drone.drone_id} has been recharged.")
            await member_drone.remove_roles(get(bot.guilds[0].roles, name=BATTERY_DRAINED))


async def recharge_battery(drone):
    '''
    Every hour, restore a portion of a drone's battery.
    This function is intended to be called from the report_storage task.
    '''
    return


async def append_battery_indicator(message, message_copy):
    '''
    Appends battery icon to messages either by prepending message content,
    or by appending display name. (e.g ⬡-Drone #0001 [|||]-)
    '''
    return False