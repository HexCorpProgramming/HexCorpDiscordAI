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

async def report_status(context):
    '''
    Creates an embed with some debug-information about the AI.
    '''

    embed = discord.Embed(
        title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
    embed.set_thumbnail(url=DRONE_AVATAR)

    embed.add_field(name='deployed commit',
                    value=read_version(), inline=False)

    await context.send(embed=embed)
