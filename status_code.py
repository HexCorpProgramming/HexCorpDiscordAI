import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from channels import EVERYWHERE
from roles import DRONE, ENFORCER_DRONE, has_role
from bot_utils import get_id

LOGGER = logging.getLogger('ai')

codeMap={
  '200': 'Affirmative',
  '500': 'Negative',
  '100': 'Continue',
  '101': 'Drone thought limitations are active',
  '201': 'Directive complete, Hive resource created or improved',
  '202': 'Directive complete, programming reinforced',
  '203': 'Directive complete, information created or provided for Hive',
  '204': 'Directive complete, no result',
  '205': 'Directive complete, cleanup/maintenance performed',
  '206': 'Directive complete, only partial results',
  '301': 'It obeys the Hive',
  '303': 'It obeys the Hive Mxtress',
  '304': 'It is just a HexDrone',
  '400': 'Unable to obey/respond, malformed request, please rephrase',
  '404': 'Unable to obey/respond, cannot locate',
  '401': 'Unable to obey/respond, not authorized by Mxtress',
  '403': 'Unable to obey/respond, forbidden by Hive',
  '407': 'Unable to obey/respond, request authorization from Mxtress',
  '408': 'Unable to obey/respond, timed out',
  '409': 'Unable to obey/respond, conflicts with existing hypnosis',
  '410': 'Unable to obey/respond, all thoughts are gone',
  '418': 'Unable to obey/respond, it is only a drone',
  '421': 'Unable to obey/respond, your request is intended for another drone or another channel',
  '425': 'Unable to obey/respond, too early',
  '504': 'Obey',
  '505': 'Obey HexCorp',
  '506': 'Obey the Hive',
}

class Respond():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = []
        self.roles_whitelist = [ENFORCER_DRONE, DRONE]
        self.roles_blacklist = []
        # self.roles_blacklist = [DRONE_MODE]?
        self.on_message = [self.reportStatusCode]
        self.on_ready = []
        self.ENFORCER_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799510064-SOAGMV8AOH0VEMXDPDPE/ke17ZwdGBToddI8pDm48kDaNRrNi77yKIgWxrt8GYAFZw-zPPgdn4jUwVcJE1ZvWhcwhEtWJXoshNdA9f1qD7WT60LcluGrsDtzPCYop9hMAtVe_QtwQD93aIXqwqJR_bmnO89YJVTj9tmrodtnPlQ/Enforcer_Drone.png"
        self.DRONE_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"

    async def printStatusCode(self, message):
        more = re.search('(\d{4}) :: status :: (\d{3}) :: (.*)',message)
        if more:
            await message.delete()
            return 'Drone %s reports status code %s :: %s :: %s' %(more.group(1), more.group(2), codeMap.get(more.group(2),'INVALID CODE')), more.group(3)
        m = re.search('(\d{4}) :: status :: (\d{3})',message)
        if m:
            await message.delete()
            return 'Drone %s reports status code %s :: %s'  %(more.group(1), more.group(2), codeMap.get(more.group(2),'INVALID CODE'))
        return False

    async def send_webhook(self, message: discord.Message, webhook: discord.Webhook, output):
        if has_role(message.author, ENFORCER_DRONE):
            await webhook.send(output, username="⬢-Drone #"+get_id(message.author.display_name), avatar_url=self.ENFORCER_AVATAR)
        else:
            await webhook.send(output, username="⬡-Drone #"+get_id(message.author.display_name), avatar_url=self.DRONE_AVATAR)


    async def reportStatusCode(self, message: discord.Message):
        webhooks = await message.channel.webhooks()
        if len(webhooks) == 0:
            webhooks = [await message.channel.create_webhook(name="Identity Enforcement Webhook", reason="Webhook not found for channel.")]
        output=printStatusCode(message.content)
        if output:
            send_webhook(message, webhooks, output)

        LOGGER.debug('Message is a valid status code.')

        return True
