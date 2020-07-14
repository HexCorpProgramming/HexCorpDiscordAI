import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from bot_utils import get_id
from channels import DRONE_DEV_CHANNELS, EVERYWHERE, STORAGE_FACILITY, DRONE_HIVE_CHANNELS, REPETITIONS
from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, ENFORCER_DRONE, DRONE, has_role, EVERYONE, MODERATION
from webhook import send_webhook_with_specific_output
from glitch import glitch_if_applicable


class Stoplights():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = DRONE_DEV_CHANNELS
        self.roles_whitelist = [EVERYONE]
        self.roles_blacklist = []
        self.on_message = [self.check_for_stoplights]
        self.on_ready = []
        self.help_content = {'name': 'Emergency Stoplight',
                             'value': 'Anyone can use a stoplight emote, even optimized drones in order to stop a scene if they feel uncomfortable.'}

    async def check_for_stoplights(self, message: discord.Message):
        important_moderator_message = ["⏰"]
        important_messages = ["🔴", "🟡", "🟢"]
        # List of any important emoji, can be updated.
        for important in important_moderator_message:

            if important in message.content:
                for role in message.guild.roles:
                # Checks for all roles in discord server.
                    if MODERATION == role.name:
                        # This checks if the moderation role is in the list of roles, and if it is, then...
                        await message.channel.send(f"Moderators needed {role.mention}!")
                        # It pings the moderators WHEN Red circle is used
                return True
        for important in important_messages:
            if important in message.content:
                return True
            # If Green or yellow circle is used, it passes all other modules.