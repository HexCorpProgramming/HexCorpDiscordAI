import re
import discord
from discord.utils import get
from bot_utils import get_id
from roles import has_role, DRONE


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
    if reaction.emoji == '🗑️' and has_role(member, DRONE) and get_id(member.display_name) == get_id(reaction.message.author.display_name):
        await reaction.message.delete()
