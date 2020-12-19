import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from resources import DRONE_AVATAR
from roles import has_role, DRONE
from db.drone_dao import is_identity_enforced

LOGGER = logging.getLogger('ai')


async def enforce_identity(message: discord.Message, message_copy):
    if has_role(message.author, DRONE) and (message.channel.name in DRONE_HIVE_CHANNELS or is_identity_enforced(message.author)):
        message_copy.avatar_url = DRONE_AVATAR


def identity_enforcable(member: discord.Member, context=None, channel=None):
    '''
    Takes a context or channel object and uses it to check if an identity should be enforced.
    '''

    if context is not None:
        return has_role(member, DRONE) and (context.channel.name in DRONE_HIVE_CHANNELS or is_identity_enforced(member))
    elif channel is not None:
        return has_role(member, DRONE) and (channel.name in DRONE_HIVE_CHANNELS or is_identity_enforced(member))
    else:
        raise ValueError("identity_enforceable must be provided a context or channel object.")
