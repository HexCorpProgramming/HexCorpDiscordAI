import re
from discord.ext.commands import check, Context, CheckFailure, PrivateMessageOnly
from src.roles import HIVE_MXTRESS, has_role, TEST_BOT
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


def dm_only() -> Callable[[T], T]:
    '''
    Only allow a command to be used in a direct message.

    This has an exception for TestBot because bots cannot DM each other.
    '''

    def predicate(ctx: Context) -> bool:
        '''
        Check that a message is in DM or from TestBot
        '''

        if not has_role(ctx.author, TEST_BOT) and ctx.guild is not None:
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
