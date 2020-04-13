import discord
import re
from channels import DRONE_HIVE_CHANNELS
from roles import DRONE, ENFORCER_DRONE, has_role
from bot_utils import get_id

class Identity_Enforcer():

    def __init__(self, bot):
        self.bot = bot
        self.on_message = [self.enforce_identity]
        self.on_ready = [self.report_online]
        self.channels = [] + DRONE_HIVE_CHANNELS
        self.roles_whitelist = [DRONE, ENFORCER_DRONE]
        self.roles_blacklist = []
        self.ENFORCER_AVATAR = "https://i.ibb.co/1GhMqhx/Enforcer-Drone.png"
        self.DRONE_AVATAR = "https://i.ibb.co/RCNvTTr/Drone.png"

    async def send_webhook(self, message: discord.Message, webhook: discord.Webhook):
        if(has_role(message.author, ENFORCER_DRONE)):
            await webhook.send(message.content, username="⬢-Drone #"+get_id(message.author.display_name), avatar_url=self.ENFORCER_AVATAR)
        else:
            await webhook.send(message.content, username="⬡-Drone #"+get_id(message.author.display_name), avatar_url=self.DRONE_AVATAR)

    async def enforce_identity(self, message: discord.Message):
        webhooks = await message.guild.webhooks()
        await message.delete()
        for webhook in webhooks:
            if webhook.channel == message.channel:
                await self.send_webhook(message, webhook)
                return False
        await self.send_webhook(message, await message.channel.create_webhook(name="Identity Enforcement Webhook", reason="Webhook not found for channel."))
        return False
    
    async def report_online(self):
        print("Identity enforcer online.")

    