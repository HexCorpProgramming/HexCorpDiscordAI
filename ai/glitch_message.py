import discord
import random
from db.drone_dao import is_glitched, is_battery_powered, get_battery_percent_remaining
import logging
import math

diacritics = list(range(0x0300, 0x036F))
DISCORD_CHAR_LIMIT = 2000
MAX_GLITCH_AMOUNT = 30
MAX_DIACRITICS_PER_MESSAGE = 60
MAX_DIACRITICS_PER_CHAR = 1

LOGGER = logging.getLogger('ai')


def glitch(message: str, glitch_amount=45):

    glitch_percentage = glitch_amount / 100

    LOGGER.debug(f"Glitching/case flipping {glitch_percentage * 100}% of characters (aprox {math.ceil(len(message) * glitch_percentage)} characters)")

    message_length = len(message)
    message_list = list(message)

    # Flip case
    for i in range(0, math.ceil(len(message) * glitch_percentage)):
        index = random.randint(0, len(message_list) - 1)
        if message_list[index].isupper():
            message_list[index] = message_list[index].lower()
        else:
            message_list[index] = message_list[index].upper()

    # Add diacritics
    max_characters_to_glitch = min(math.ceil(len(message) * glitch_percentage), MAX_DIACRITICS_PER_MESSAGE)
    LOGGER.debug(f"Adding diacritics to {max_characters_to_glitch} characters.")
    for i in range(0, min(int(max_characters_to_glitch), DISCORD_CHAR_LIMIT - message_length)):
        if len("".join(message_list)) >= DISCORD_CHAR_LIMIT:
            break
        index = random.randint(0, len(message_list) - 1)
        if len(message_list[index]) - 1 < MAX_DIACRITICS_PER_CHAR:
            message_list[index] += chr(random.choice(diacritics))

    LOGGER.debug(f"Glitched message: {''.join(message_list)}")

    return "".join(message_list)


async def glitch_if_applicable(message: discord.Message, message_copy):
    if is_glitched(message.author):
        glitch_amount = MAX_GLITCH_AMOUNT
    elif is_battery_powered(message.author) and get_battery_percent_remaining(message.author) < 30:
        glitch_amount = MAX_GLITCH_AMOUNT - get_battery_percent_remaining(message.author)
        glitch_amount *= 2
    else:
        return False

    LOGGER.info(f"Glitching message for {message.author.display_name}")
    LOGGER.debug(f"Glitch amount: {glitch_amount}")

    message_copy.content = glitch(message_copy.content, glitch_amount)

    return False
