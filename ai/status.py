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

def get_list_of_commands(context):
    cmd_list = []
    for command in context.bot.commands:
        cmd_list.append(command.name)
    return cmd_list

def get_list_of_listeners(listeners):
    lis_list = []
    for listener in listeners:
        lis_list.append(listener.__name__)
    return lis_list

async def report_status(context, listeners):
    '''
    Creates an embed with some debug information about the AI.
    '''

    embed = discord.Embed(
        title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
    embed.set_thumbnail(url=DRONE_AVATAR)

    embed.add_field(name='deployed commit',
                    value=read_version(), inline=False)
    embed.add_field(name='registered commands', value=get_list_of_commands(context), inline=False)
    embed.add_field(name='message listeners', value=get_list_of_listeners(listeners), inline=False)

    await context.send(embed=embed)
