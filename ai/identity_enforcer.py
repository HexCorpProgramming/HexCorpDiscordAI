import logging
import re

import discord

from bot_utils import get_id
from channels import DRONE_HIVE_CHANNELS
from roles import DRONE, ENFORCER_DRONE, has_role
from ai.speech_optimization import informative_status_code_regex, plain_status_code_regex
from webhook import send_webhook

LOGGER = logging.getLogger('ai')

class Identity_Enforcer():

    def __init__(self, bot):
        self.bot = bot
        self.on_message = [self.enforce_identity]
        self.on_ready = [self.report_online]
        self.channels_whitelist = DRONE_HIVE_CHANNELS
        self.channels_blacklist = []
        self.roles_whitelist = [DRONE, ENFORCER_DRONE]
        self.roles_blacklist = []
        self.informative_status_code_regex = re.compile(informative_status_code_regex)
        self.plain_status_code_regex = re.compile(plain_status_code_regex)
  
    def check_is_status_code(self, message):
        return self.informative_status_code_regex.match(message.content) or self.plain_status_code_regex.match(message.content)

    async def enforce_identity(self, message: discord.Message):
        if not self.check_is_status_code(message):
            webhooks = await message.channel.webhooks()
            if len(webhooks) == 0:
                webhooks = [await message.channel.create_webhook(name="Identity Enforcement Webhook", reason="Webhook not found for channel.")]
            await message.delete()
            await send_webhook(message, webhooks[0])
        return False
    
    async def report_online(self):
        LOGGER.info("Identity enforcer online.")
