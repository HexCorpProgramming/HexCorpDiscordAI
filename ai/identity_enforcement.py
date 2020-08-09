import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from webhook import send_webhook, get_webhook_for_channel
from roles import has_role, HIVE_MXTRESS

LOGGER = logging.getLogger('ai')


async def enforce_identity(message: discord.Message):

    if message.channel.name not in DRONE_HIVE_CHANNELS or has_role(message.author, HIVE_MXTRESS):
        return

    await message.delete()
    webhook = await get_webhook_for_channel(message.channel)
    await send_webhook(message, webhook)
