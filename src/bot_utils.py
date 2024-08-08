import re
from discord.ext.commands import check, command as bot_command, Context, CheckFailure, PrivateMessageOnly
from src.roles import HIVE_MXTRESS, has_any_role, has_role, MODERATION_ROLES, TEST_BOT
from typing import Any, Callable, Coroutine, Iterable, Optional, TypeVar
from functools import wraps
from src.log import LogContext

COMMAND_PREFIX = 'hc!'
T = TypeVar('T')
CommandFuncType = Callable[..., Coroutine[Any, Any, None]]
CommandFuncDecoratorType = Callable[[CommandFuncType], CommandFuncType]


def fetch(collection: Iterable[T], **kwargs: Any) -> T:
    '''
    Find an item in a collection with the given property.

    Example:

    member = fetch(guild.members, id=12345)

    Returns an item from the collection.

    Raise an Exception if no item was found.
    '''

    key, value = next(iter(kwargs.items()))

    for item in collection:
        if getattr(item, key) == value:
            return item

    raise Exception('Item not found')


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


def moderator_only() -> Callable[[T], T]:
    '''
    Only allow a command to be used by users with a moderation role.
    '''

    def predicate(ctx: Context) -> bool:
        '''
        Check that the message's author is a moderator.
        '''

        return has_any_role(ctx.author, MODERATION_ROLES)

    return check(predicate)


def dm_only() -> Callable[[T], T]:
    '''
    Only allow a command to be used in a direct message.

    This has an exception for TestBot because bots cannot DM each other.
    '''

    def predicate(ctx: Context) -> bool:
        '''
        Check that the message was sent privately, not in a channel.

        There is an exception for TestBot because one bot cannot DM another.
        '''

        if ctx.guild is not None and not has_role(ctx.author, TEST_BOT):
            raise PrivateMessageOnly()

        return True

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
    Override discord.command to start a logging context for the command.
    '''

    bot_decorator = bot_command(*args, **kwargs)

    def decorator(func: CommandFuncType) -> CommandFuncType:
        '''
        The original command decorator for the command function wrapped in a logging context.
        '''

        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            '''
            Begin a new logging context and call the original function.
            '''

            with LogContext('Command ' + func.__qualname__ + '()'):
                await func(*args, **kwargs)

        return bot_decorator(wrapper)

    return decorator
