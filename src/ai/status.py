import logging
from pathlib import Path
from collections.abc import Callable, Coroutine
from typing import Any, List
from discord import Embed, Message
from discord.ext.commands import Cog, Context
from src.bot_utils import channels_only, command

from src.bot_utils import COMMAND_PREFIX
from src.channels import BOT_DEV_COMMS
from src.resources import DRONE_AVATAR

LOGGER = logging.getLogger('ai')

ListenerType = Callable[[Message, Any | None], Coroutine[Any, Any, bool]]


class StatusCog(Cog):
    '''
    The command handler for the "ai_status" command.
    '''

    def __init__(self, message_listeners: List[ListenerType]):
        self.message_listeners = message_listeners

    @channels_only(BOT_DEV_COMMS)
    @command(usage=f'{COMMAND_PREFIX}ai_status')
    async def ai_status(self, context: Context):
        '''
        A debug command, that displays information about the AI.
        '''

        await report_status(context, self.message_listeners)


def read_version() -> str:
    '''
    Read and return the currently checked-out branch from Git.

    Returns an error message on failure.
    '''

    try:
        return Path('.git/HEAD').read_text()
    except:  # noqa: E722
        return '[unable to read version information]'


def get_list_of_commands(context: Context):
    '''
    Get a list of all the commands available on the bot.
    '''

    return sorted([command.name for command in context.bot.commands])


def get_list_of_listeners(listeners: List[ListenerType]):
    '''
    Get a list of all the message listener function names.
    '''

    return sorted([listener.__name__ for listener in listeners])


async def report_status(context: Context, listeners: List[ListenerType]):
    '''
    Creates an embed with some debug information about the AI.
    '''

    embed = Embed(title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
    embed.set_thumbnail(url=DRONE_AVATAR)

    embed.add_field(name='deployed commit', value=read_version(), inline=False)
    embed.add_field(name='registered commands', value=get_list_of_commands(context), inline=False)
    embed.add_field(name='message listeners', value=get_list_of_listeners(listeners), inline=False)

    await context.send(embed=embed)
