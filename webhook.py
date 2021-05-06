import discord
import logging
from ai.data_objects import MessageCopy
import io

LOGGER = logging.getLogger("ai")


async def proxy_message_by_webhook(message_content, message_username=None, message_avatar=None, message_attachments=None, webhook=None, channel=None, embed=None):
    '''
    Proxies a message via webhook. If a webhook is not provided, one will be retrieved via the channel object passed as a parameter.
    If neither a webhook or channel object are passed, this function will do nothing.
    Message content is mandatory. If no username or avatar are provided, the message will be proxied with webhook defaults.
    '''

    if webhook is None and channel is not None:
        webhook = await get_webhook_for_channel(channel)

    if webhook is None:
        LOGGER.warn(f"Failed to retrieve a webhook. Could not proxy message: '{message_content}'")
        return False

    await webhook.send(message_content, avatar_url=message_avatar, username=message_username, files=message_attachments, embed=embed)


async def get_webhook_for_channel(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        # No webhook available, create one.
        return_webhook = await channel.create_webhook(name="AI Webhook")
    else:
        return_webhook = webhooks[0]

    return return_webhook


async def webhook_if_message_altered(original: discord.Message, copy: MessageCopy):
    '''
    This function calls the proxy_message_by_webhook function if the message copy
    has been altered in any way by the on_message event listeners in main.py
    '''
    if original.content != copy.content or original.author.display_name != copy.display_name or original.author.avatar_url != copy.avatar_url or original.attachments != copy.attachments:
        LOGGER.info("Proxying altered message.")

        LOGGER.info("Converting all attachments")
        # Convert available Attachment objects into File objects.
        attachments_as_files = []
        for attachment in copy.attachments:
            if isinstance(attachment, discord.File):
                attachments_as_files.append(attachment)
            else:
                attachments_as_files.append(discord.File(io.BytesIO(await attachment.read()), filename=attachment.filename))
        LOGGER.info("Attachments converted.")

        embed = None
        if original.reference:
            referenced_message: discord.Message = original.reference.resolved
            reply_text = f"[Reply to]({referenced_message.jump_url}): {referenced_message.content}"
            embed = discord.Embed(color=0xff66ff, description=reply_text)
            embed.set_author(name=referenced_message.author.display_name, icon_url=referenced_message.author.avatar_url)

        await original.delete()
        await proxy_message_by_webhook(message_content=copy.content,
                                       message_username=copy.display_name,
                                       message_avatar=copy.avatar_url,
                                       message_attachments=attachments_as_files,
                                       channel=original.channel,
                                       webhook=None,
                                       embed=embed)
