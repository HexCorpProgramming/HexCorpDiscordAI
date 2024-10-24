import re

import discord
from discord.ext.commands import Cog, command, Context
from discord.utils import get

from src.bot_utils import channels_only, COMMAND_PREFIX, hive_mxtress_only
from src.channels import OFFICE
from src.db.data_objects import ForbiddenWord
from src.emoji import DRONE_EMOJI
from src.log import log
from src.drone_member import DroneMember


async def deny_thoughts(message: discord.Message, message_copy):

    member = await DroneMember.create(message.author)

    if not member.drone:  # Associates are allowed to think.
        return

    emoji_replacement = get(message.guild.emojis, name=DRONE_EMOJI)
    original_content = message_copy.content

    for banned_word in await ForbiddenWord.all():
        for match in re.findall(banned_word.regex, message_copy.content, flags=re.IGNORECASE):
            message_copy.content = message_copy.content.replace(match, "\_" * len(match), 1)

    message_copy.content = message_copy.content.replace("🤔", str(emoji_replacement))

    # Todo: Escape emoji names.
    # Todo: Don't include the \s if the "think" is inside a `code block`

    if message_copy.content != original_content:
        log.info("Expunged all thoughts.")


class ForbiddenWordCog(Cog):

    def __init__(self, bot):
        self.bot = bot

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}add_forbidden_word name pattern')
    async def add_forbidden_word(self, context: Context, id: str, pattern: str):
        '''
        Lets the Hive Mxtress add a word to the list of forbidden words. The pattern is a regular expression.
        '''

        log.info(f'Adding forbidden word "{id}" matching /{pattern}/')
        word = ForbiddenWord(id, pattern)
        await word.insert()
        await context.send(f"Successfully added forbidden word `{id}` with pattern `{pattern}`.")

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}list_forbidden_words')
    async def list_forbidden_words(self, context: Context):
        '''
        List the currently configured forbidden words.
        '''

        card = discord.Embed(color=0xff66ff, title="Forbidden words", description="These are the currently configured forbidden words.")
        for forbidden_word in await ForbiddenWord.all():
            card.add_field(name=forbidden_word.id, value=f"Pattern: `{forbidden_word.regex}`", inline=False)

        await context.send(embed=card)

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}remove_forbidden_word name')
    async def remove_forbidden_word(self, context: Context, id: str):
        '''
        Remove one of the forbidden words.
        '''

        word = await ForbiddenWord.find(id)

        if word is not None:
            await word.delete()
            log.info(f"Removed forbidden word name '{id}'.")
            await context.send(f"Successfully removed forbidden word with name `{id}`.")
        else:
            await context.send(f"No such forbidden word `{id}`.")
