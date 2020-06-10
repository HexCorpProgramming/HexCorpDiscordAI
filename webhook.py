import discord

from bot_utils import get_id
from channels import DRONE_HIVE_CHANNELS
from roles import DRONE, ENFORCER_DRONE, has_role

from glitch import glitch_if_applicable

from resources import *

async def send_webhook_with_specific_output(message: discord.Message, webhook: discord.Webhook, output):
    if message.channel.name in DRONE_HIVE_CHANNELS:
        if has_role(message.author, ENFORCER_DRONE):
            await webhook.send(glitch_if_applicable(output, message.author), username=f"⬢-Drone #{get_id(message.author.display_name)}", avatar_url=ENFORCER_AVATAR)
        else:
            await webhook.send(glitch_if_applicable(output, message.author), username=f"⬡-Drone #{get_id(message.author.display_name)}", avatar_url=DRONE_AVATAR)
    else:
        await webhook.send(glitch_if_applicable(output, message.author), username=message.author.display_name, avatar_url=message.author.avatar_url)

async def send_webhook(message: discord.Message, webhook: discord.Webhook):
    await send_webhook_with_specific_output(message, webhook, message.content)

async def get_webhook_for_channel(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        #No webhook available, create one.
        return_webhook = await channel.create_webhook(name = "AI Webhook")
    else:
        return_webhook = webhooks[0]

    return return_webhook