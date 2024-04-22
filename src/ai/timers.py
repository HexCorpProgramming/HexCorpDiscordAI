from datetime import datetime

from discord.ext import commands, tasks
from discord.utils import get

from src.ai.drone_configuration import set_can_self_configure
from src.db.database import connect
from src.db.drone_dao import update_droneOS_parameter
from src.db.timer_dao import delete_timer, get_timers_elapsed_before
from src.display_names import update_display_name
from src.roles import (GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT,
                       SPEECH_OPTIMIZATION, BATTERY_POWERED)
from src.log import log
from src.drone_member import DroneMember

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
    @connect()
    async def process_timers(self):
        '''
        Check for elapsed timers and disable configs if any are found.
        '''

        log.debug("Checking for elapsed timers.")

        for elapsed_timer in await get_timers_elapsed_before(datetime.now()):
            drone_member = DroneMember(self.bot.guilds[0].get_member(elapsed_timer.discord_id))
            await update_droneOS_parameter(drone_member, elapsed_timer.mode, False)
            await delete_timer(elapsed_timer.id)
            await drone_member.remove_roles(get(self.bot.guilds[0].roles, name=MODE_TO_ROLE[elapsed_timer.mode]))
            await update_display_name(drone_member)
            await set_can_self_configure(drone_member)
            log.info(f"Elapsed timer for {drone_member.display_name}; toggled off {elapsed_timer.mode}")
