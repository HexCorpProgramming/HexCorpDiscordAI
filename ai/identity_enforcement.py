import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from webhook import send_webhook, get_webhook_for_channel

LOGGER = logging.getLogger('ai')


async def enforce_identity(message: discord.Message):

    if message.channel.name not in DRONE_HIVE_CHANNELS:
        return

    await message.delete()
    webhook = await get_webhook_for_channel(message.channel)
    await send_webhook(message, webhook)
