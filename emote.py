import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from channels import (CREATIVE_LABOR_CHANNEL, GAMER_DRONE_LOBBY_CHANNEL,
                      LEWD_CREATIVE_LABOR_CHANNEL, LEWD_TRANSMISSIONS_CHANNEL,
                      MINECRAFT_DIRECTION_CHANNEL, TRANSMISSIONS_CHANNEL)
from roles import ASSOCIATE, DRONE, DRONE_MODE, HIVE_MXTRESS, has_role

LOGGER = logging.getLogger('ai')

BASE_EMOJI_LENGTH = 27
ADDTL_EXCLAMATION_LENGTH = 14
ADDTL_QUESTION_LENGTH = 11
ADDTL_COMMA_LENGTH = 4
CHARACTER_LIMIT = 2000

valid_characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                    'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9']
exceptional_characters = {' ': 'blank', '/': 'hex_slash', '.': 'hex_dot',
                          '?': 'hex_questionmark', '!': 'hex_exclamationmark', ',': 'hex_comma', '0': 'hex_o'}


def message_is_an_acceptable_length(message):
    LOGGER.info("Message is: " + message)
    return CHARACTER_LIMIT > (
        (len(message) * BASE_EMOJI_LENGTH) +
        (message.count("!") * ADDTL_EXCLAMATION_LENGTH) +
        (message.count("?") * ADDTL_QUESTION_LENGTH) +
        (message.count(",") * ADDTL_COMMA_LENGTH)
    )


def clean_message(message):
    # Removes custom emojis (<:name:id>)
    return re.sub(r'<:\w*:\d*>', '', message)


class Emote():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [TRANSMISSIONS_CHANNEL,
                                   LEWD_TRANSMISSIONS_CHANNEL,
                                   CREATIVE_LABOR_CHANNEL,
                                   LEWD_CREATIVE_LABOR_CHANNEL,
                                   GAMER_DRONE_LOBBY_CHANNEL,
                                   MINECRAFT_DIRECTION_CHANNEL]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS, ASSOCIATE, DRONE]
        self.roles_blacklist = [DRONE_MODE]
        self.on_message = [self.emote]
        self.on_ready = [self.report_online]
        self.help_content = {
            'name': 'emote', 'value': 'let the AI say stuff with emotes e.g. `emote uwu`'}

    async def report_online(self):
        LOGGER.debug("Emote cog online.")

    async def emote(self, message: discord.Message):
        if not message.content.lower().startswith('emote '):
            return False

        cleaned_message = clean_message(message.content[6:].lower())
        if message_is_an_acceptable_length(cleaned_message):

            message_to_output = ""
            colon_found = False

            for character in cleaned_message:
                emoji_name = ""  # Reset emoji name.

                if character in valid_characters:
                    emoji_name = "hex_"+character

                elif character in exceptional_characters:
                    emoji_name = exceptional_characters[character]

                # Special handling for double colons since it needs to know if the previous character was a colon too.
                elif character == ':' and colon_found == True:
                    emoji_name = "hex_dc"
                # Setting the flag for the next iteration. colon_found is checked to be not true to avoid false positives on repetitions (i.e :::)
                colon_found = character == ":" and not colon_found

                # If a valid emoji has been found, append it.
                if get(self.bot.emojis, name=emoji_name) != None:
                    message_to_output += str(get(self.bot.emojis,
                                                 name=emoji_name))
            LOGGER.debug("Emote cog: Sending message of length [" + str(
                len(message_to_output)) + "] and content " + message_to_output)
            if len(message_to_output) != 0:
                await message.channel.send("> " + message_to_output)
        else:
            await message.channel.send("That message is too long.")

        return True
