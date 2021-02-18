import logging
import re

import discord
from discord.ext.commands import Cog, command, guild_only
from discord.utils import get

from channels import DRONE_HIVE_CHANNELS
from bot_utils import COMMAND_PREFIX

LOGGER = logging.getLogger('ai')

valid_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                    'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9']
exceptional_characters = {' ': 'blank', '/': 'hex_slash', '.': 'hex_dot',
                          '?': 'hex_questionmark', '!': 'hex_exclamationmark', ',': 'hex_comma', '0': 'hex_o'}


class EmoteCog(Cog):

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}emote "beep boop"', aliases=['big', 'emote'])
    async def bigtext(self, context, sentence):
        '''
        Let the AI say things using emotes.
        '''
        if context.channel.name not in DRONE_HIVE_CHANNELS:
            reply = generate_big_text(context.channel, sentence)
            if reply:
                await context.send(reply)


def clean_sentence(sentence):
    # Removes custom emojis (<:name:id>) and returns the lowercase version
    return re.sub(r'<:(.*?):\d{18}>', '', sentence).lower()


def generate_big_text(channel: discord.TextChannel, sentence):

    LOGGER.debug("In generate_big_text function.")

    LOGGER.debug("Sanatizing sentence of custom emojis.")

    sentence = clean_sentence(sentence)

    reply = ""

    colon_before = False

    for character in sentence:

        emoji_name = None

        if character in valid_characters:
            emoji_name = f"hex_{character}"
        elif character in exceptional_characters:
            emoji_name = f"{exceptional_characters[character]}"
        if character == ':' and colon_before:
            emoji_name = "hex_dc"

        colon_before = character == ":" and not colon_before

        if emoji_name is not None and (emoji := get(channel.guild.emojis, name=emoji_name)) is not None:
            reply += str(emoji)

    message_length = len(reply)
    LOGGER.debug(f"About to send big-text message of length {message_length}")

    if message_length > 0 and message_length <= 2000:
        LOGGER.info(f"Sending big-text message of length {message_length} and content '{sentence}'")
        return f"> {reply}"
    elif message_length > 2000:
        LOGGER.info("big-text message was too long to send.")
        return None
    else:
        LOGGER.debug("big-text request message contained no acceptable content.")
        return None
