import logging
import discord
import re
from db.drone_dao import is_drone
from db.forbidden_word_dao import get_all_forbidden_words
from discord.utils import get
from emoji import DRONE_EMOJI
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
