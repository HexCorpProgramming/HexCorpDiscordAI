import re
import discord
from discord.utils import get


PATTERN_REACTS = {
    r'^(\d{4}) :: Code `109` :: .*': 'gooddrone'
}


async def parse_for_reactions(message: discord.Message, message_copy=None) -> bool:
    '''
    Look for patterns and react with an emote if one matches.
    '''
    for (pattern, emote_name) in PATTERN_REACTS.items():
        if re.match(pattern, message.content):
            await message.add_reaction(get(message.guild.emojis, name=emote_name))

    return False
