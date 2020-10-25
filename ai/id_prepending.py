import discord
from db.drone_dao import is_prepending_id
import bot_utils
import logging
from bot_utils import COMMAND_PREFIX

LOGGER = logging.getLogger('ai')


async def check_if_prepending_necessary(message: discord.Message):
    if is_prepending_id(message.author):
        drone_id = bot_utils.get_id(message.author.display_name)
        if message.content.startswith(f"{drone_id} :: ") or message.content.startswith(COMMAND_PREFIX):
            return False
        else:
            LOGGER.info("Deleting message that did not begin with ID prependment.")
            await message.delete()
            return True
    else:
        return False
