import re

import discord
from discord.ext.commands import Cog, command, guild_only, UserInputError
from discord.utils import get

from src.channels import DRONE_HIVE_CHANNELS
from src.bot_utils import channels_only, COMMAND_PREFIX
from src.log import log

valid_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                    'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9']
exceptional_characters = {' ': 'blank', '/': 'hex_slash', '.': 'hex_dot',
                          '?': 'hex_questionmark', '!': 'hex_exclamationmark', ',': 'hex_comma', '0': 'hex_o'}


class EmoteCog(Cog):

    @guild_only()
    @channels_only(*DRONE_HIVE_CHANNELS)
    @command(usage=f'{COMMAND_PREFIX}emote "beep boop"', aliases=['big', 'emote'])
    async def bigtext(self, context, *, sentence: str):
        '''
        Let the AI say things using emotes.
        '''

        reply = generate_big_text(context.channel, sentence)

        message_length = len(reply)

        if message_length > 2000:
            raise UserInputError('Message is too long.')

        if message_length == 0:
            raise UserInputError('Message contained no acceptable content.')

        log.info('Emoting: ' + sentence)
        await context.send('> ' + reply)


def clean_sentence(sentence):
    '''
    Remove custom emojis (<:name:id>) and returns the lowercase version.
    '''

    return re.sub(r'<:(.*?):\d{18}>', '', sentence).lower()


def generate_big_text(channel: discord.TextChannel, sentence):
    '''
    Replace text with matching emojis.
    '''

    sentence = clean_sentence(sentence)

    reply = ""

    colon_before = False

    for character in sentence:

        emoji_name = None

        if character in valid_characters:
            emoji_name = f"hex_{character}"
        elif character in exceptional_characters:
            emoji_name = f"{exceptional_characters[character]}"
        elif character == ':' and colon_before:
            emoji_name = "hex_dc"

        colon_before = character == ":" and not colon_before

        if emoji_name is not None and (emoji := get(channel.guild.emojis, name=emoji_name)) is not None:
            reply += str(emoji)

    return reply
