import re
from discord.ext.commands import check, command as bot_command, Context, CheckFailure
from src.db.database import connect
from src.roles import HIVE_MXTRESS, has_role
from typing import Callable, Optional, TypeVar

COMMAND_PREFIX = 'hc!'
T = TypeVar("T")


def channels_only(*channels: str) -> Callable[[T], T]:
    '''
    Only allow a command to be used within the given channels.
    Channels is a list of channel names.
    '''

    channel_names = ', '.join(['#' + c for c in channels])

    def predicate(ctx: Context) -> bool:
        '''
        Check that the message's context is one of the allowed channels.
        '''

        if ctx.guild is None or ctx.channel.name not in channels:
            raise CheckFailure(f'The {ctx.command.name} command is only available in {channel_names}')

        return True

    # Attach the list of permitted channels to the predicate so it can be inspected by the help command.
    predicate.channels = channel_names

    return check(predicate)


def hive_mxtress_only() -> Callable[[T], T]:
    '''
    Only allow a command to be used by the Hive Mxtress.
    '''

    def predicate(ctx: Context) -> bool:
        '''
        Check that the message's author is the Hive Mxtress.
        '''
        return has_role(ctx.author, HIVE_MXTRESS)

    return check(predicate)


def get_id(username: str) -> Optional[str]:
    '''
    Find the four digit ID in a nickname or None if no such ID is found.
    '''
    found = re.search(r"\d{4}", username)
    if found is None:
        return None
    else:
        return found.group()


def command(*args, **kwargs):
    '''
    Decorator factory to register a bot command.

    Returns a decorator.
    '''

    def decorator(func):
        '''
        Create and return a wrapper around a command function.
        '''

        connect_args = {}

        if 'db' in kwargs:
            connect_args['filename'] = kwargs['db']
            del kwargs['db']

        connect_func = connect(**connect_args)(func)

        # Set the command's name to the name of the wrapped function.
        if 'name' not in kwargs:
            kwargs['name'] = func.__name__

        # The command is referred to both by command.name and command.callback.__name__.
        # They both need to be the same, and to match the name of the command function.
        # Override the name here so it's the same as the command function's name.
        connect_func.__name__ = kwargs['name']
        connect_func.__wrapped__ = func

        bot_func = bot_command(*args, **kwargs)(connect_func)

        # Register the command on the bot if a bot was specified.
        if 'parent' in kwargs:
            kwargs['parent'].add_command(bot_func)

        return bot_func

    return decorator
