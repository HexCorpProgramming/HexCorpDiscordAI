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

from resources import CLOCK, TRAFFIC_LIGHTS

async def check_for_stoplights(message: discord.Message):
    if CLOCK in message.content:
        moderator_role = get(message.guild.roles, name=MODERATION)
        await message.channel.send(f"Moderators needed {moderator_role.mention}!")
        return True
    else:
        return any(traffic_light in message.content for traffic_light in TRAFFIC_LIGHTS)
