import logging
import asyncio
from datetime import datetime
from discord.utils import get

from db.timer_dao import get_timers_elapsed_before, delete_timer
from db.drone_dao import fetch_drone_with_drone_id, update_droneOS_parameter

from roles import GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT, SPEECH_OPTIMIZATION
from id_converter import convert_id_to_member
from display_names import update_display_name

LOGGER = logging.getLogger('ai')

MODE_TO_ROLE = {
    'optimized': SPEECH_OPTIMIZATION,
    'glitched': GLITCHED,
    'id_prepending': ID_PREPENDING,
    'identity_enforcement': IDENTITY_ENFORCEMENT
}


async def start_process_timers(bot):
    while True:
        await asyncio.sleep(60)
        await process_timers(bot)


async def process_timers(bot):
    '''
    Check for elapsed timers and disable configs if any are found.
    '''
    for elapsed_timer in get_timers_elapsed_before(datetime.now()):
        drone = fetch_drone_with_drone_id(elapsed_timer.drone_id)
        drone_member = convert_id_to_member(bot.guilds[0], drone.drone_id)

        update_droneOS_parameter(drone_member, elapsed_timer.mode, False)
        delete_timer(elapsed_timer.id)
        await drone_member.remove_roles(get(bot.guilds[0].roles, name=MODE_TO_ROLE[elapsed_timer.mode]))
        await update_display_name(drone_member)
        LOGGER.info(f"Elapsed timer for {drone_member.display_name}; toggled off {elapsed_timer.mode}")
