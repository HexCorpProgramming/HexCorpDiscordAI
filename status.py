from pathlib import Path
import roles
from channels import BOT_DEV_COMMS
import logging
import discord

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
        self.embed_thumbnail = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"
        self.modules = modules

    async def report_status(self, message: discord.Message):
        '''
        Creates an embed with some debug-information about the AI.
        '''
        if message.content.lower() != 'ai_status':
            return False

        embed = discord.Embed(title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
        embed.set_thumbnail(url=self.embed_thumbnail)

        embed.add_field(name='deployed commit', value=read_version(), inline=False)
        embed.add_field(name='active modules', value=[module.__class__.__name__ for module in self.modules], inline=False)

        await message.channel.send(embed=embed)
        return False


