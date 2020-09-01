import discord
from roles import VOICE, has_role
from discord.utils import get

from datetime import datetime, timedelta


NOT_A_MEMBER = 'Access denied: you are not a member of this server.'
ACCESS_DENIED = 'Access denied: you have not been on the server for long enough to gain access to voice chat.'
ACCESS_ALREADY_GRANTED = 'You already have access to voice channels.'
ACCESS_GRANTED = 'Access granted.'


async def add_voice(context, guild: discord.Guild):
    member = guild.get_member(context.channel.recipient.id)

    if member is None:
        await context.channel.send(NOT_A_MEMBER)
        return

    if member.joined_at > datetime.now() - timedelta(weeks=2):
        await context.channel.send(ACCESS_DENIED)
        return
    if has_role(member, VOICE):
        await context.channel.send(ACCESS_ALREADY_GRANTED)
        return

    await member.add_roles(get(guild.roles, name=VOICE))
    await context.channel.send(ACCESS_GRANTED)
