import discord
import random
from db.drone_dao import is_glitched, is_battery_powered, get_battery_percent_remaining
import logging
import math
import re

diacritics = list(range(0x0300, 0x036F))
DISCORD_CHAR_LIMIT = 2000
MAX_GLITCH_AMOUNT = 30
MAX_DIACRITICS_PER_MESSAGE = 60
MAX_DIACRITICS_PER_CHAR = 1

LOGGER = logging.getLogger('ai')

custom_emoji_regex = re.compile(r'<:(.*?):\d{18}>')


def glitch(message: str, glitch_amount=45):

    LOGGER.info(f"Glitching message: {message}")

    glitch_percentage = glitch_amount / 100

    LOGGER.debug(f"Glitching/case flipping {glitch_percentage * 100}% of characters (aprox {math.ceil(len(message) * glitch_percentage)} characters)")

    full_message_length = len(message)

    custom_emojis = []

    # Temporarily remove custom emojis
    for custom_emoji in re.finditer(custom_emoji_regex, message):
        LOGGER.debug(f"Custom emoji found at position {custom_emoji.start()}: {custom_emoji}")
        custom_emojis.append((custom_emoji.group(), max(0, custom_emoji.start())))
        message = re.sub(pattern=custom_emoji_regex, repl='', string=message, count=1)
        LOGGER.debug(f"Custom emoji removed. Current message: {message}")

    message_list = list(message)

    LOGGER.debug(f"Message list without custom emojis: {message_list}")

    if message_list == []:
        LOGGER.info("Not glitching message (message empty).")
        return ''.join(emoji for emoji, index in custom_emojis)

    # Flip case
    for i in range(0, math.ceil(len(message_list) * glitch_percentage)):
        index = random.randint(0, len(message_list) - 1)
        try:
            if message_list[index].isupper():
                message_list[index] = message_list[index].lower()
            else:
                message_list[index] = message_list[index].upper()
        except IndexError:
            LOGGER.warn(f"Index error. Length of list: {len(message_list)} Index: {index}")

    # Add diacritics
    max_characters_to_glitch = min(math.ceil(len(message) * glitch_percentage), MAX_DIACRITICS_PER_MESSAGE)
    LOGGER.debug(f"Adding diacritics to {max_characters_to_glitch} characters.")
    for i in range(0, min(int(max_characters_to_glitch), DISCORD_CHAR_LIMIT - full_message_length)):
        if len("".join(message_list)) >= DISCORD_CHAR_LIMIT:
            break
        index = random.randint(0, len(message_list) - 1)
        if len(message_list[index]) - 1 < MAX_DIACRITICS_PER_CHAR:
            message_list[index] += chr(random.choice(diacritics))

    # Add custom emojis back in
    for custom_emoji, reinsertion_index in custom_emojis:
        try:
            message_list[reinsertion_index:reinsertion_index] = list(custom_emoji)
        except IndexError:
            LOGGER.warn(f"Bad index. Desired: {reinsertion_index} Length: {len(message_list)}")

    LOGGER.debug(f"Final glitched message list: {message_list}")

    return "".join(message_list)


async def glitch_if_applicable(message: discord.Message, message_copy):
    if is_glitched(message.author):
        glitch_amount = MAX_GLITCH_AMOUNT * 2
    elif is_battery_powered(message.author) and get_battery_percent_remaining(message.author) < 30:
        glitch_amount = MAX_GLITCH_AMOUNT - get_battery_percent_remaining(message.author)
        glitch_amount *= 2
    else:
        LOGGER.info("Not glitching message (drone is neither glitched nor low battery).")
        return False

    LOGGER.info(f"Glitching message for {message.author.display_name}")
    LOGGER.debug(f"Glitch amount: {glitch_amount}")

    message_copy.content = glitch(message_copy.content, glitch_amount)

    return False
