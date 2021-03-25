from bot_utils import get_id
from discord.ext import tasks
from db.drone_dao import is_drone, is_battery_powered, deincrement_battery_minutes_remaining
from id_converter import convert_id_to_member
import logging

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


@tasks.loop(seconds=1)
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
    LOGGER.info("Tracking drained batteries.")


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