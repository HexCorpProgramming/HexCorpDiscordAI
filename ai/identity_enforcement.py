import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from webhook import send_webhook, get_webhook_for_channel
from roles import has_role, DRONE
from db.drone_dao import is_identity_enforced

LOGGER = logging.getLogger('ai')


async def enforce_identity(message: discord.Message):
    if has_role(message.author, DRONE) and (message.channel.name in DRONE_HIVE_CHANNELS or is_identity_enforced(message.author)):
        await message.delete()
        webhook = await get_webhook_for_channel(message.channel)
        await send_webhook(message, webhook)
