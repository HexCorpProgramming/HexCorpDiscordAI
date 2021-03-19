import copy
from bot_utils import get_id
from discord.ext import tasks
from db.drone_dao import is_battery_powered

MAX_BATTERY_CAPACITY_HOURS = 8
MAX_BATTERY_CAPACITY_MINS = MAX_BATTERY_CAPACITY_HOURS * 60

draining_batteries = {}


async def drain_battery(message, message_copy=None):
    '''
    If message author has battery DroneOS config enabled, begin or restart
    the task to drain 1 minute of battery per minute, for 15 minutes.
    '''

    if not is_battery_powered(message.author):
        return False

    drone_id = get_id(message.author.display_name)
    
    if draining_batteries.get(drone_id) is None:
        print("No drain record found. Starting task.")
        drain_battery_task = copy.copy(drain_battery_source)
        drain_battery_task.start(drone_id)
        draining_batteries[drone_id] = drain_battery_task
    else:
        draining_batteries[drone_id].current_loop = 0


@tasks.loop(seconds=3, count=5)
async def drain_battery_source(drone):
    '''
    This task should not be started directly. Make a copy of it and start that
    instead, so that multiple drones can be tracked as their batteries are drained.
    '''
    print(f"Draining battery of {drone}")


@drain_battery_source.after_loop
async def drain_battery_finished():
    print("Finished battery drain.")


@drain_battery_source.before_loop
async def drain_battery_begin():
    print("Beginning battery drain.")

async def recharge_battery(drone):
    '''
    Every hour, restore a portion of a drone's battery.
    This function is intended to be called from the report_storage task.
    '''
    return


async def append_battery_indicator():
    '''
    Appends battery icon to messages either by prepending message content,
    or by appending display name. (e.g ⬡-Drone #0001 [|||]-)
    '''
    return False