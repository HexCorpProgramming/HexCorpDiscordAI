import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from roles import has_role, HIVE_MXTRESS
from resources import DRONE_AVATAR

LOGGER = logging.getLogger('ai')


async def enforce_identity(message: discord.Message, message_copy):

    if message.channel.name not in DRONE_HIVE_CHANNELS or has_role(message.author, HIVE_MXTRESS):
        return

    message_copy.avatar_url = DRONE_AVATAR
