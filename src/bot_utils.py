import re
from typing import Callable, Optional, TypeVar
from discord.ext.commands import check, Context, PrivateMessageOnly

COMMAND_PREFIX = 'hc!'
T = TypeVar('T')


def get_id(username: str) -> Optional[str]:
    '''
    Find the four digit ID in a nickname or None if no such ID is found.
    '''
    found = re.search(r"\d{4}", username)
    if found is None:
        return None
    else:
        return found.group()


def dm_only() -> Callable[[T], T]:
    '''
    A decorator factory for making a command only usable in a direct message.

    This has an exception for TestBot because one bot cannot DM another.
    '''

    def predicate(ctx: Context) -> bool:
        '''
        Raise a PrivateMessageOnly exception if the message is not a DM,
        unless the sender is TestBot.
        '''

        if ctx.guild is not None and ctx.author.name != 'TestBot':
            raise PrivateMessageOnly()

        return True

    return check(predicate)
