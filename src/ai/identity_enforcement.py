import discord

from src.ai.data_objects import MessageCopy
from src.channels import (DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY,
                          MODERATION_CATEGORY)
from src.db.drone_dao import is_drone, is_identity_enforced


async def enforce_identity(message: discord.Message, message_copy: MessageCopy):
    if await identity_enforcable(message.author, channel=message.channel):
        message_copy.identity_enforced = True


async def identity_enforcable(member: discord.Member, channel=None):
    '''
    Takes a context or channel object and uses it to check if the identity of a user should be enforced.
    '''

    if channel is not None:
        return await is_drone(member) and (channel.name in DRONE_HIVE_CHANNELS or await is_identity_enforced(member)) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]
    else:
        raise ValueError("identity_enforceable must be provided a context or channel object.")
