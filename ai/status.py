import logging
from pathlib import Path

import discord

import roles
from channels import BOT_DEV_COMMS
from resources import DRONE_AVATAR

LOGGER = logging.getLogger('ai')


def read_version() -> str:
    if not Path('.git').exists():
        return '[unable to read version information]'

    return Path('.git/HEAD').read_text()


class Status():
    '''
    This module can give a short report on the AI.
    '''

    def __init__(self, bot, modules):
        self.bot = bot
        self.channels_whitelist = [BOT_DEV_COMMS]
        self.channels_blacklist = []
        self.roles_whitelist = [roles.EVERYONE]
        self.roles_blacklist = []
        self.on_message = [self.report_status]
        self.on_ready = []
        self.help_content = {'name': 'ai_status',
                             'value': 'get a status report from the AI'}
        self.modules = modules

    async def report_status(self, message: discord.Message):
        '''
        Creates an embed with some debug-information about the AI.
        '''
        if message.content.lower() != 'ai_status':
            return False

        embed = discord.Embed(
            title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
        embed.set_thumbnail(url=DRONE_AVATAR)

        embed.add_field(name='deployed commit',
                        value=read_version(), inline=False)
        embed.add_field(name='active modules', value=[
                        module.__class__.__name__ for module in self.modules], inline=False)

        await message.channel.send(embed=embed)
        return False
