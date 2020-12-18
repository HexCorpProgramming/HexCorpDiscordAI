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
