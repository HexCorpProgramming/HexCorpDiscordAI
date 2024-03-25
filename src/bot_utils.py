import re
from typing import Optional
from src.db.database import connect
from discord.ext.commands import command as bot_command

COMMAND_PREFIX = 'hc!'


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
