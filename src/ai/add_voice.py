from datetime import datetime, timedelta, timezone

import discord
from discord.ext.commands import Cog, dm_only
from discord.utils import get

from src.resources import BRIEF_DM_ONLY
from src.roles import VOICE, has_role
from src.bot_utils import command, COMMAND_PREFIX

NOT_A_MEMBER = 'Access denied: you are not a member of this server.'
ACCESS_DENIED = 'Access denied: you have not been on the server for long enough to gain access to voice chat.'
ACCESS_ALREADY_GRANTED = 'You already have access to voice channels.'
ACCESS_GRANTED = 'Access granted.'


class AddVoiceCog(Cog):

    def __init__(self, bot):
        self.bot = bot

    @dm_only()
    @command(usage=f'{COMMAND_PREFIX}request_voice_role', brief=[BRIEF_DM_ONLY])
    async def request_voice_role(self, context):
        '''
        Gives you the Voice role and thus access to voice channels if you have been on the server for more than 2 weeks.
        '''
        await add_voice(context, self.bot.guilds[0])


async def add_voice(context, guild: discord.Guild):
    member = guild.get_member(context.message.author.id)

    if member is None:
        await context.channel.send(NOT_A_MEMBER)
        return

    if member.joined_at > datetime.now(timezone.utc) - timedelta(weeks=2):
        await context.channel.send(ACCESS_DENIED)
        return
    if has_role(member, VOICE):
        await context.channel.send(ACCESS_ALREADY_GRANTED)
        return

    await member.add_roles(get(guild.roles, name=VOICE))
    await context.channel.send(ACCESS_GRANTED)
