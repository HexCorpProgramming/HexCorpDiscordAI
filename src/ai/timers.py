import logging
from datetime import datetime

from discord.ext import commands, tasks
from discord.utils import get

from src.ai.drone_configuration import set_can_self_configure
from src.db.drone_dao import fetch_drone_with_drone_id, update_droneOS_parameter
from src.db.timer_dao import delete_timer, get_timers_elapsed_before
from src.display_names import update_display_name
from src.id_converter import convert_id_to_member
from src.roles import (GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT,
                       SPEECH_OPTIMIZATION, BATTERY_POWERED)

LOGGER = logging.getLogger('ai')

MODE_TO_ROLE = {
    'optimized': SPEECH_OPTIMIZATION,
    'glitched': GLITCHED,
    'id_prepending': ID_PREPENDING,
    'identity_enforcement': IDENTITY_ENFORCEMENT,
    'is_battery_powered': BATTERY_POWERED
}


class TimersCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=1)
    async def process_timers(self):
        '''
        Check for elapsed timers and disable configs if any are found.
        '''

        LOGGER.info("Checking for elapsed timers.")

        for elapsed_timer in get_timers_elapsed_before(datetime.now()):
            drone = fetch_drone_with_drone_id(elapsed_timer.drone_id)
            drone_member = convert_id_to_member(self.bot.guilds[0], drone.drone_id)
            update_droneOS_parameter(drone_member, elapsed_timer.mode, False)
            delete_timer(elapsed_timer.id)
            await drone_member.remove_roles(get(self.bot.guilds[0].roles, name=MODE_TO_ROLE[elapsed_timer.mode]))
            await update_display_name(drone_member)
            set_can_self_configure(drone_member)
            LOGGER.info(f"Elapsed timer for {drone_member.display_name}; toggled off {elapsed_timer.mode}")
