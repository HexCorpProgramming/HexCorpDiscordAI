import io

import discord

from src.ai.data_objects import MessageCopy
from src.log import log
from src.resources import DRONE_AVATAR


async def proxy_message_by_webhook(message_content, message_username=None, message_avatar=None, message_attachments=None, webhook=None, channel=None, embed=None) -> discord.WebhookMessage:
    '''
    Proxies a message via webhook. If a webhook is not provided, one will be retrieved via the channel object passed as a parameter.
    If neither a webhook or channel object are passed, this function will do nothing.
    Message content is mandatory. If no username or avatar are provided, the message will be proxied with webhook defaults.
    '''

    if webhook is None and channel is not None:
        webhook = await get_webhook_for_channel(channel)

    if webhook is None:
        log.warn(f"Failed to retrieve a webhook. Could not proxy message: '{message_content}'")
        return False

    return await webhook.send(message_content, avatar_url=message_avatar, username=message_username, files=message_attachments, embed=embed, wait=True)


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
    content_differs = original.content != copy.content
    display_name_differs = original.author.display_name != copy.display_name
    avatar_differs = original.author.display_avatar.url != copy.avatar.url
    attachments_differ = original.attachments != copy.attachments
    if any([content_differs, display_name_differs, avatar_differs, attachments_differ, copy.identity_enforced]):
        log.info("Proxying altered message.")

        # Convert available Attachment objects into File objects.
        attachments_as_files = []
        for attachment in copy.attachments:
            if isinstance(attachment, discord.File):
                attachments_as_files.append(attachment)
            else:
                attachments_as_files.append(discord.File(io.BytesIO(await attachment.read()), filename=attachment.filename))

        # create an embed when responding to another message
        embed = None
        if original.reference:
            referenced_message: discord.Message = original.reference.resolved
            reply_text = f"[Reply to]({referenced_message.jump_url}): {referenced_message.content}"

            # trim down overly long messages
            if len(reply_text) > 277:
                reply_text = reply_text[:277] + "..."

            embed = discord.Embed(color=0xff66ff, description=reply_text)
            embed.set_author(name=referenced_message.author.display_name, icon_url=referenced_message.author.avatar)

        # Don't try to send an empty message.  This might happen if a message is deleted.
        if copy.content == '' and embed is None:
            return

        await original.delete()
        created_message = await proxy_message_by_webhook(message_content=copy.content,
                                                         message_username=copy.display_name,
                                                         message_avatar=copy.avatar.url if not copy.identity_enforced else DRONE_AVATAR,
                                                         message_attachments=attachments_as_files,
                                                         channel=original.channel,
                                                         webhook=None,
                                                         embed=embed)

        # add reacts from the original message
        for reaction in original.reactions:
            await created_message.add_reaction(reaction)
