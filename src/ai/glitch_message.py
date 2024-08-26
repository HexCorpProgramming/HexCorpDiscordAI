import io
import logging
import math
import random
import re
from typing import List, Union

import discord
import glitch_this
from PIL import Image

from src.ai.data_objects import MessageCopy
from src.channels import HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.db.drone_dao import (get_battery_percent_remaining, is_battery_powered,
                              is_glitched)

LOGGER = logging.getLogger("ai")

diacritics = list(range(0x0300, 0x036F))
DISCORD_CHAR_LIMIT = 2000
MAX_GLITCH_AMOUNT = 30
MAX_DIACRITICS_PER_MESSAGE = 60
MAX_DIACRITICS_PER_CHAR = 1
glitcher = glitch_this.ImageGlitcher()

LOGGER = logging.getLogger('ai')

protected_text_regex = re.compile(r'(<:(.*?):\d{18}>)|(\|\|.*\|\|)|(https?://\S+)')


def escape_characters(message: str, characters_regex):
    escaped_characters = []
    modified_message = message

    for custom_emoji in re.finditer(characters_regex, message):
        LOGGER.debug(f"Custom emoji found at position {custom_emoji.start()}: {custom_emoji}")
        escaped_characters.append((custom_emoji.group(), max(0, custom_emoji.start())))
        modified_message = re.sub(pattern=characters_regex, repl='', string=modified_message, count=1)
        LOGGER.debug(f"Custom emoji removed. Current message: {message}")

    return escaped_characters, modified_message


def glitch_text(message: str, glitch_amount=45) -> str:

    LOGGER.info(f"Glitching message: {message}")

    glitch_percentage = glitch_amount / 100

    LOGGER.debug(f"Glitching/case flipping {glitch_percentage * 100}% of characters (aprox {math.ceil(len(message) * glitch_percentage)} characters)")

    message_length_with_emoji: int = len(message)

    # Temporarily remove custom emojis, spoilered text and hyperlinks
    escaped_characters, modified_message = escape_characters(message, protected_text_regex)

    message_list = list(modified_message)

    message_length_without_emoji: int = len(message_list)

    # Count diacritics so message length != >2000 when custom emojis readded.
    added_diacritics: int = 0

    LOGGER.debug(f"Message list without custom emojis: {message_list}")

    if message_list == []:
        LOGGER.info("Not glitching message (message empty).")
        return ''.join(emoji for emoji, index in escaped_characters)

    # Flip case
    for i in range(0, math.ceil(len(message_list) * glitch_percentage)):
        index = random.randint(0, message_length_without_emoji - 1)
        try:
            if message_list[index].isupper():
                message_list[index] = message_list[index].lower()
            else:
                message_list[index] = message_list[index].upper()
        except IndexError:
            LOGGER.warn(f"Index error. Length of list: {len(message_list)} Index: {index}")

    # Add diacritics
    max_characters_to_glitch = min(math.ceil(len(modified_message) * glitch_percentage), MAX_DIACRITICS_PER_MESSAGE)
    LOGGER.debug(f"Adding diacritics to {max_characters_to_glitch} characters.")
    for i in range(0, min(int(max_characters_to_glitch), DISCORD_CHAR_LIMIT - message_length_with_emoji)):
        if added_diacritics + message_length_with_emoji >= DISCORD_CHAR_LIMIT:
            break
        index = random.randint(0, len(message_list) - 1)
        if len(message_list[index]) - 1 < MAX_DIACRITICS_PER_CHAR:
            message_list[index] += chr(random.choice(diacritics))
            added_diacritics += 1

    # Add custom emojis back in
    for custom_emoji, reinsertion_index in escaped_characters:
        try:
            message_list[reinsertion_index:reinsertion_index] = list(custom_emoji)
        except IndexError:
            LOGGER.warn(f"Bad index. Desired: {reinsertion_index} Length: {len(message_list)}")

    LOGGER.debug(f"Final glitched message list: {message_list}")

    return "".join(message_list)


async def glitch_images(attachments: List[discord.Attachment], glitch_amount=45) -> List[Union[discord.Attachment, discord.File]]:
    # glitch attached images
    # the data flow is:
    # CDN -> raw bytes -> BytesIO -> PIL Image -> glitch_this -> PIL Image -> BytesIO -> CDN
    processed_attachments = []
    for attachment in attachments:
        # only images have dimensions
        if attachment.height is not None:
            attachment_bytes = io.BytesIO(await attachment.read())
            pillow = Image.open(attachment_bytes)
            glitched_pillow = glitcher.glitch_image(pillow, max(0.1, glitch_amount / 10))
            glitched_bytes = io.BytesIO()
            glitched_pillow.save(glitched_bytes, "PNG")
            glitched_bytes.seek(0)
            glitched_attachment = discord.File(glitched_bytes, filename=attachment.filename)
            processed_attachments.append(glitched_attachment)
        else:
            processed_attachments.append(attachment)

    return processed_attachments


async def calc_glitch_amount(drone: discord.Member) -> int:
    if await is_glitched(drone):
        return MAX_GLITCH_AMOUNT * 2
    elif await is_battery_powered(drone) and await get_battery_percent_remaining(drone) < 30:
        return (MAX_GLITCH_AMOUNT - await get_battery_percent_remaining(message.author)) * 2
    else:
        return 0


async def glitch_if_applicable(message: discord.Message, message_copy: MessageCopy):
    # No glitching in the moderation channels
    if message.channel.category.name in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]:
        return False

    glitch_amount = await calc_glitch_amount(message.author)

    if glitch_amount == 0:
        LOGGER.info("Not glitching message (drone is neither glitched nor low battery).")
        return False

    LOGGER.info(f"Glitching message for {message.author.display_name}, glitch amount: {glitch_amount}")

    message_copy.content = glitch_text(message_copy.content, glitch_amount)

    message_copy.attachments = await glitch_images(message.attachments, glitch_amount)

    return False
