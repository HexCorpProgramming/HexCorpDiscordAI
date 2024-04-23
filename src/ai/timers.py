from discord.ext import commands, tasks
from discord.utils import get

from src.db.database import connect
from src.db.data_objects import Timer
from src.roles import (GLITCHED, ID_PREPENDING, IDENTITY_ENFORCEMENT,
                       SPEECH_OPTIMIZATION, BATTERY_POWERED, THIRD_PERSON_ENFORCEMENT)
from src.log import log

MODE_TO_ROLE = {
    'optimized': SPEECH_OPTIMIZATION,
    'glitched': GLITCHED,
    'id_prepending': ID_PREPENDING,
    'identity_enforcement': IDENTITY_ENFORCEMENT,
    'third_person_enforcement': THIRD_PERSON_ENFORCEMENT,
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

        for member in await Timer.all_elapsed(self.bot.guilds[0]):
            setattr(member.drone, member.drone.timer.mode, False)
            await member.drone.save()
            await member.drone.timer.delete()

            await member.remove_roles(get(self.bot.guilds[0].roles, name=MODE_TO_ROLE[member.drone.timer.mode]))
            await member.update_display_name()
            await member.drone.update_self_configuration()
            log.info(f"Elapsed timer for {member.display_name}; toggled off {member.drone.timer.mode}")
