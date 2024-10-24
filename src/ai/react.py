import re

import discord
from discord.utils import get

from src.roles import DRONE, has_role

PATTERN_REACTS = {
    r'^(\d{4}) :: 109( :: .*)?': 'gooddrone'
}


async def parse_for_reactions(message: discord.Message, message_copy=None) -> bool:
    '''
    Look for patterns and react with an emote if one matches.
    '''
    for (pattern, emote_name) in PATTERN_REACTS.items():
        if re.match(pattern, message.content):
            await message.add_reaction(get(message.guild.emojis, name=emote_name))

    return False


async def delete_marked_message(reaction: discord.Reaction, member: discord.Member):
    if reaction.emoji == '🗑️' and has_role(member, DRONE) and member.id == reaction.message.author.id:
        await reaction.message.delete()
