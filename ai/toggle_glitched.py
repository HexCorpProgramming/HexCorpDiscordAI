import logging

import discord
from discord.ext import commands
from discord.utils import get

from channels import EVERYWHERE
from roles import HIVE_MXTRESS ,GLITCHED, has_role


LOGGER = logging.getLogger('ai')

class Toggle_Glitched():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.glitch]
        self.on_ready = []
        self.help_content = {'name': 'toggle_drone_corruption_levels', 'value': 'give a drone the glitched role; this command can only be used by the Hive Mxtress'}

    async def glitch(self, message: discord.Message):

        if not message.content.lower().startswith('toggle_drone_corruption_levels '):
            return False

        LOGGER.debug('Message is valid for toggling the glitched role.')

        for target_drone in message.mentions:
            if has_role(target_drone, GLITCHED):
                await message.channel.send(f"{target_drone.display_name} is not glitched anymore.")
                await target_drone.remove_roles(get(message.guild.roles, name=GLITCHED))
            else:
                await message.channel.send(f"{target_drone.display_name} is now glitched.")
                await target_drone.add_roles(get(message.guild.roles, name=GLITCHED))

        return True
