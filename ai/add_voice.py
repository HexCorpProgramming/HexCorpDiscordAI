import discord
from roles import VOICE, has_role
from discord.utils import get

from datetime import datetime, timedelta


async def add_voice(context, guild: discord.Guild):
    member = guild.get_member(context.channel.recipient.id)
    if member.joined_at > datetime.now() - timedelta(weeks=2):
        await context.channel.send('Access denied: you have not been on the server for long enough to gain access to voice chat.')
        return
    if has_role(member, VOICE):
        await context.channel.send('You already have access to voice channels.')
        return

    await member.add_roles(get(guild.roles, name=VOICE))
    await context.channel.send('Access granted.')
