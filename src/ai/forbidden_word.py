import logging
import re

import discord
from discord.ext.commands import Cog, command, Context, guild_only
from discord.utils import get

from src.bot_utils import COMMAND_PREFIX
from src.channels import OFFICE
from src.db.data_objects import ForbiddenWord
from src.db.drone_dao import is_drone
from src.db.forbidden_word_dao import (delete_forbidden_word_by_id,
                                       get_all_forbidden_words,
                                       insert_forbidden_word)
from src.emoji import DRONE_EMOJI
from src.resources import BRIEF_HIVE_MXTRESS
from src.roles import HIVE_MXTRESS, has_role

LOGGER = logging.getLogger("ai")


async def deny_thoughts(message: discord.Message, message_copy):

    if not await is_drone(message.author):  # Associates are allowed to think.
        return

    emoji_replacement = get(message.guild.emojis, name=DRONE_EMOJI)

    LOGGER.info("Expunging all thoughts.")
    for banned_word in await get_all_forbidden_words():
        for match in re.findall(banned_word.regex, message_copy.content, flags=re.IGNORECASE):
            message_copy.content = message_copy.content.replace(match, "\_" * len(match), 1)

    message_copy.content = message_copy.content.replace("🤔", str(emoji_replacement))

    # Todo: Escape emoji names.
    # Todo: Don't include the \s if the "think" is inside a `code block`


class ForbiddenWordCog(Cog):

    def __init__(self, bot):
        self.bot = bot

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}add_forbidden_word name pattern', brief=[BRIEF_HIVE_MXTRESS])
    async def add_forbidden_word(self, context: Context, id: str, pattern: str):
        '''
        Lets the Hive Mxtress add a word to the list of forbidden words. The pattern is a regular expression.
        '''
        if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
            await insert_forbidden_word(ForbiddenWord(id, pattern))
            await context.send(f"Successfully added forbidden word `{id}` with pattern `{pattern}`.")
        else:
            await context.send("This command can only be used by the Hive Mxtress in their office.")

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}list_forbidden_words', brief=[BRIEF_HIVE_MXTRESS])
    async def list_forbidden_words(self, context: Context):
        '''
        List the currently configured forbidden words.
        '''
        if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
            card = discord.Embed(color=0xff66ff, title="Forbidden words", description="These are the currently configured forbidden words.")
            for forbidden_word in await get_all_forbidden_words():
                card.add_field(name=forbidden_word.id, value=f"Pattern: `{forbidden_word.regex}`", inline=False)

            await context.send(embed=card)
        else:
            await context.send("This command can only be used by the Hive Mxtress in their office.")

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}remove_forbidden_word name', brief=[BRIEF_HIVE_MXTRESS])
    async def remove_forbidden_word(self, context: Context, id: str):
        '''
        Remove one of the forbidden words.
        '''
        if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
            await delete_forbidden_word_by_id(id)
            await context.send(f"Successfully removed forbidden word with name `{id}`.")
        else:
            await context.send("This command can only be used by the Hive Mxtress in their office.")
