import discord

from src.bot_utils import COMMAND_PREFIX
from src.channels import HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.log import log
from src.drone_member import DroneMember


async def check_if_prepending_necessary(message: discord.Message, message_copy=None):
    member = await DroneMember.create(message.author)

    if member.drone and member.drone.id_prepending and message.channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]:
        if message.content.startswith(f"{member.drone.drone_id} :: ") or message.content.startswith(COMMAND_PREFIX):
            return False
        else:
            log.info("Deleting message that did not begin with ID prependment.")
            await message.delete()
            return True
    else:
        return False
