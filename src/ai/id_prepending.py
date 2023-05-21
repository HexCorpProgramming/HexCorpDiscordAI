import logging

import discord

from src.bot_utils import COMMAND_PREFIX, get_id
from src.channels import HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.db.drone_dao import is_prepending_id

LOGGER = logging.getLogger('ai')


async def check_if_prepending_necessary(message: discord.Message, message_copy=None):
    if is_prepending_id(message.author) and message.channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]:
        drone_id = get_id(message.author.display_name)
        if message.content.startswith(f"{drone_id} :: ") or message.content.startswith(COMMAND_PREFIX):
            return False
        else:
            LOGGER.info("Deleting message that did not begin with ID prependment.")
            await message.delete()
            return True
    else:
        return False
