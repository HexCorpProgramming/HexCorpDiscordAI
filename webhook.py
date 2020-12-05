import discord

from channels import DRONE_HIVE_CHANNELS

from glitch import glitch_if_applicable

from resources import DRONE_AVATAR


async def send_webhook_with_specific_output(channel: discord.TextChannel, author: discord.Member, webhook: discord.Webhook, output: str):
    if channel.name in DRONE_HIVE_CHANNELS:
        await webhook.send(glitch_if_applicable(output, author), username=author.display_name, avatar_url=DRONE_AVATAR)
    else:
        await webhook.send(glitch_if_applicable(output, author), username=author.display_name, avatar_url=author.avatar_url)


async def send_webhook(message: discord.Message, webhook: discord.Webhook):
    await send_webhook_with_specific_output(message.channel, message.author, webhook, message.content)


async def get_webhook_for_channel(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        # No webhook available, create one.
        return_webhook = await channel.create_webhook(name="AI Webhook")
    else:
        return_webhook = webhooks[0]

    return return_webhook
