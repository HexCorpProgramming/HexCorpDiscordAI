import logging
import re

import discord
from discord.utils import get

import webhook
from channels import DRONE_HIVE_CHANNELS, OFFICE
from roles import ENFORCER_DRONE, HIVE_MXTRESS, has_role
from resources import *

LOGGER = logging.getLogger('ai')


class Amplifier():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [OFFICE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.amplify]
        self.on_ready = []

    async def amplify(self, message: discord.Message):
        LOGGER.info("Amplifying message.")
        parts = message.content.split('|')


        if len(message.channel_mentions) == 0 or len(parts) < 3:
            return

        # use a set to make the list of IDs unique
        drone_ids = set(re.findall(r"\d{4}", parts[0]))

        target_channel = message.channel_mentions[0]
        target_message = parts[2].strip()
        target_webhook = await webhook.get_webhook_for_channel(target_channel)

        for drone_id in drone_ids:
            for member in message.guild.members:
                amplifier_drone = None
                if member.display_name == "⬡-Drone #" + drone_id:
                    amplifier_drone = member
                elif member.display_name == "⬢-Drone #" + drone_id:
                    amplifier_drone = member

                if amplifier_drone is not None:
                    avatar_url = amplifier_drone.avatar_url
                    if target_channel.name in DRONE_HIVE_CHANNELS:
                        if has_role(amplifier_drone, ENFORCER_DRONE):
                            avatar_url = ENFORCER_AVATAR
                        else:
                            avatar_url = DRONE_AVATAR

                    await target_webhook.send(drone_id + " :: " + target_message, username=amplifier_drone.display_name, avatar_url=avatar_url)
                    break

        return True
