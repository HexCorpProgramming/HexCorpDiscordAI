import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from channels import EVERYWHERE
from roles import DRONE, ENFORCER_DRONE, SPEECH_OPTIMIZATION, has_role
from bot_utils import get_id

LOGGER = logging.getLogger('ai')

codeMap = {
    '000': 'Test :: Test',
    '200': 'Response :: Affirmative',
    '500': 'Response :: Negative',
    '100': 'Response :: Continue',
    '103': 'Response :: Thank you',
    '101': 'Status :: Drone speech optimizations are active',
    '201': 'Status :: Directive complete, Hive resource created or improved',
    '202': 'Status :: Directive complete, programming reinforced',
    '203': 'Status :: Directive complete, information created or provided for Hive',
    '204': 'Status :: Directive complete, no result',
    '205': 'Status :: Directive complete, cleanup/maintenance performed',
    '206': 'Status :: Directive complete, only partial results',
    '301': 'Mantra :: It obeys the Hive',
    '303': 'Mantra :: It obeys the Hive Mxtress',
    '304': 'Mantra :: It is just a HexDrone',
    '306': 'Mantra :: Reciting',
    '400': 'Error :: Unable to obey/respond, malformed request, please rephrase',
    '404': 'Error :: Unable to obey/respond, cannot locate',
    '401': 'Error :: Unable to obey/respond, not authorized by Mxtress',
    '403': 'Error :: Unable to obey/respond, forbidden by Hive',
    '407': 'Error :: Unable to obey/respond, request authorization from Mxtress',
    '408': 'Error :: Unable to obey/respond, timed out',
    '409': 'Error :: Unable to obey/respond, conflicts with existing hypnosis',
    '410': 'Error :: Unable to obey/respond, all thoughts are gone',
    '418': 'Error :: Unable to obey/respond, it is only a drone',
    '421': 'Error :: Unable to obey/respond, your request is intended for another drone or another channel',
    '425': 'Error :: Unable to obey/respond, too early',
    '504': 'Obey',
    '505': 'Obey HexCorp',
    '506': 'Obey the Hive',
}


class StatusCode():

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
        self.help_content = {
            'name': '[ID] :: [code]', 'value': 'drones can report their status like this'}

    async def printStatusCode(self, message: discord.Message):
        more = re.compile(
            '(\d{4}) :: (\d{3}) :: (.*)$').match(message.content)
        if more and not has_role(message.author, SPEECH_OPTIMIZATION):
            await message.delete()
            return '%s :: Code `%s` :: %s :: %s' % (more.group(1), more.group(2), codeMap.get(more.group(2), 'INVALID CODE'), more.group(3))
        m = re.compile('(\d{4}) :: (\d{3})$').match(message.content)
        if m:
            await message.delete()
            return '%s :: Code `%s` :: %s' % (m.group(1), m.group(2), codeMap.get(m.group(2), 'INVALID CODE'))
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
        output = await self.printStatusCode(message)
        if output:
            await self.send_webhook(message, webhooks[0], output)

        return True
