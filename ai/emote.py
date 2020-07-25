import logging
import re

import discord
from discord.ext import commands
from discord.utils import get
from channels import DRONE_HIVE_CHANNELS

LOGGER = logging.getLogger('ai')

valid_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                    'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9']
exceptional_characters = {' ': 'blank', '/': 'hex_slash', '.': 'hex_dot',
                          '?': 'hex_questionmark', '!': 'hex_exclamationmark', ',': 'hex_comma', '0': 'hex_o'}

def clean_sentence(sentence):
    # Removes custom emojis (<:name:id>)
    return re.sub(r'<:.*:\d*>', '', sentence)

async def generate_big_text(channel: discord.TextChannel, sentence):

    LOGGER.debug("In generate_big_text function.")

    if channel.name in DRONE_HIVE_CHANNELS: return #No fun allowed.

    LOGGER.debug("Sanatizing sentence of custom emojis.")

    sentence = clean_sentence(sentence)

    reply = ""

    for character in sentence:

        emoji_name = None

        if character in valid_characters:
            emoji_name = f"hex_{character}"
        elif character in exceptional_characters:
            emoji_name = f"hex_{exceptional_characters[character]}"
        if character == ':' and colon_before == True:
            emoji_name = "hex_dc"

        colon_before = character == ":" and not colon_before

        if emoji_name is not None and (emoji := get(channel.guild.emojis, name=emoji_name)) is not None:
            reply += str(emoji)

    
    message_length = len(reply)
    LOGGER.debug(f"About to send big-text message of length {message_length}")

    if message_length > 0 and message_length <= 2000:
        LOGGER.info(f"Sending big-text message of length {message_length} and content '{sentence}'")
        await channel.send(f"> {reply}")
    elif message_length > 2000:
        LOGGER.info(f"big-text message was too long to send.")
        await channel.send("That message is too long to embiggen.")
    else:
        LOGGER.debug("big-text request message contained no acceptable content.")