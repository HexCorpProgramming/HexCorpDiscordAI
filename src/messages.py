import discord
import src.roles as roles
from discord.utils import get
from typing import List
import random
from src.log import log

# 1 hour is 60 seconds times 60 minutes
DELETE_TIMEOUT = 60 * 60


async def delete_request(message: discord.Message, reject_message=None):
    # do not delete messages by moderators
    if any([get(message.guild.roles, name=moderation_role) in message.author.roles for moderation_role in roles.MODERATION_ROLES]):
        return

    await message.delete()

    if reject_message is not None:
        await message.channel.send(f'{message.author.mention}: {reject_message}', delete_after=DELETE_TIMEOUT)


async def answer(channel: discord.TextChannel, recipient: discord.Member, category: List[str]):
    response = random.choice(category)
    log.info('Answering with ' + response)
    await channel.send(f'{recipient.mention}: {response}')
