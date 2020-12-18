import discord
import logging
from channels import DRONE_HIVE_CHANNELS
from glitch import glitch_if_applicable
from resources import DRONE_AVATAR

LOGGER = logging.getLogger("ai")


async def send_webhook_with_specific_output(channel: discord.TextChannel, author: discord.Member, webhook: discord.Webhook, output: str, identity_enforced: bool = False):
    if channel.name in DRONE_HIVE_CHANNELS or identity_enforced:
        await webhook.send(glitch_if_applicable(output, author), username=author.display_name, avatar_url=DRONE_AVATAR)
    else:
        await webhook.send(glitch_if_applicable(output, author), username=author.display_name, avatar_url=author.avatar_url)


async def send_webook_with_really_specific_output(channel: discord.TextChannel, display_name: str, avatar_url: str, content: str):
    webhook = await get_webhook_for_channel(channel)
    await webhook.send(content, username=display_name, avatar_url=avatar_url)


async def send_webhook(message: discord.Message, webhook: discord.Webhook):
    await send_webhook_with_specific_output(message.channel, message.author, webhook, message.content, True)


async def get_webhook_for_channel(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        # No webhook available, create one.
        return_webhook = await channel.create_webhook(name="AI Webhook")
    else:
        return_webhook = webhooks[0]

    return return_webhook


async def webhook_if_content_altered(original: discord.Message, copy):
    if original.content != copy.content or original.author.display_name != copy.display_name or original.author.avatar_url != copy.avatar_url:
        LOGGER.info(f"""
        Message content altered.
        Original: {original.content}
        New: {copy.content}
        """)
        await original.delete()
        await send_webook_with_really_specific_output(original.channel, copy.display_name, copy.avatar_url, copy.content)
    else:
        LOGGER.info(f"""
        Message content unaltered.
        Original: {original.content}
        New: {copy.content}
        """)
