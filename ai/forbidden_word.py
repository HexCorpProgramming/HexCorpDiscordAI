import logging
import discord
from discord.ext.commands import Cog, command, guild_only, Context
import re

from channels import OFFICE
from db.data_objects import ForbiddenWord
from db.drone_dao import is_drone
from db.forbidden_word_dao import get_all_forbidden_words, insert_forbidden_word
from discord.utils import get
from bot_utils import COMMAND_PREFIX
from emoji import DRONE_EMOJI
from roles import HIVE_MXTRESS, has_role
LOGGER = logging.getLogger("ai")


async def deny_thoughts(message: discord.Message, message_copy):

    if not is_drone(message.author):  # Associates are allowed to think.
        return

    emoji_replacement = get(message.guild.emojis, name=DRONE_EMOJI)

    LOGGER.info("Expunging all thoughts.")
    for banned_word in get_all_forbidden_words():
        for match in re.findall(banned_word.regex, message_copy.content, flags=re.IGNORECASE):
            message_copy.content = message_copy.content.replace(match, "\_" * len(match), 1)

    message_copy.content = message_copy.content.replace("🤔", str(emoji_replacement))

    # Todo: Escape emoji names.
    # Todo: Don't include the \s if the "think" is inside a `code block`


class ForbiddenWordCog(Cog):

    def __init__(self, bot):
        self.bot = bot

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}add_forbidden_word name pattern', brief="Hive Mxtress")
    async def add_forbidden_word(self, context: Context, id: str, pattern: str):
        if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
            insert_forbidden_word(ForbiddenWord(id, pattern))
            await context.send(f"Successfully added forbidden word `{id}` with pattern `{pattern}`.")
        else:
            await context.send("This command can only be used by the Hive Mxtress in their office.")
