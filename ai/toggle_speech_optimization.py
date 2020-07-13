import logging

import discord
from discord.ext import commands
from discord.utils import get

from channels import EVERYWHERE

from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, has_role


LOGGER = logging.getLogger('ai')

class Toggle_Speech_Optimization():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]#MODERATION FOR TESTING REMOVE ON LINK TO MAIN AI
        self.roles_blacklist = []
        self.on_message = [self.dronemode]
        self.on_ready = []
        self.help_content = {'name': 'toggle_speech_optimization', 'value': 'optimize drone speech patterns; this command can only be used by the Hive Mxtress'}

    async def dronemode(self, message: discord.Message):

        if not message.content.lower().startswith('toggle_speech_optimization '):
            return False

        LOGGER.debug('Message is valid for toggling speech optimization.')

        for target_drone in message.mentions:
            if has_role(target_drone, SPEECH_OPTIMIZATION):
                await message.channel.send(f"Speech optimization deactivated for {target_drone.display_name}")
                await target_drone.remove_roles(get(message.guild.roles, name=SPEECH_OPTIMIZATION))
            else:
                await message.channel.send(f"Speech optimization activated for {target_drone.display_name}")
                await target_drone.add_roles(get(message.guild.roles, name=SPEECH_OPTIMIZATION))

        return True
