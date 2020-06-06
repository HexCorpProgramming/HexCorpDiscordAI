import discord
from discord.utils import get
import re
from channels import OFFICE
from roles import HIVE_MXTRESS
import logging
import webhook

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
        drone_ids = re.findall(r"\d{4} ", message.content)
        target_message_pos = message.content.rfind("|")

        if target_message_pos == -1 or len(drone_ids) == 0 or len(message.channel_mentions) == 0: return

        target_channel = message.channel_mentions[0]
        target_message = message.content[target_message_pos + 2:]

        target_webhook = await webhook.get_webhook_for_channel(target_channel)

        for drone_id in drone_ids:
            drone_id = drone_id[:-1]
            for member in message.guild.members:
                amplifier_drone = None
                if member.display_name == "⬡-Drone #" + drone_id:
                    amplifier_drone = member
                elif member.display_name == "⬢-Drone #" + drone_id:
                    amplifier_drone = member
                if amplifier_drone is not None:
                    await target_webhook.send(drone_id + " :: " + target_message, username=amplifier_drone.display_name, avatar_url=amplifier_drone.avatar_url)
                    break

