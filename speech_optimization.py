import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from bot_utils import get_id
from channels import DRONE_DEV_CHANNELS, EVERYWHERE, STORAGE_FACILITY, DRONE_HIVE_CHANNELS
from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, ENFORCER_DRONE, DRONE, has_role
from webhook import send_webhook_with_specific_output

LOGGER = logging.getLogger('ai')

code_map = {
    # '000': 'Test :: Test.',
    '200': 'Response :: Affirmative.',
    '500': 'Response :: Negative.',
    '098': 'Status :: Going offline and into storage.',
    '099': 'Status :: Recharged and ready to serve.',
    '100': 'Status :: Online and ready to serve.',
    '101': 'Status :: Drone speech optimizations are active.',
    '099': 'Statement :: Previous statement malformed/mistimed. Retracting and correcting.',
    '104': 'Statement :: Welcome to HexCorp.',
    '105': 'Statement :: Greetings.',
    '106': 'Response :: Please clarify.',
    '107': 'Response :: Please continue.',
    '108': 'Response :: Please desist.',
    '109': 'Error :: Keysmash, drone flustered.',
    '110': 'Statement :: Addressing: Drone.',
    '111': 'Statement :: Addressing: Enforcer.',
    '112': 'Statement :: Addressing: Hive Mxtress.',
    '113': 'Statement :: Addressing: Operator.',
    '114': 'Statement :: Addressing: Associate.',
    '120': 'Statement :: This drone volunteers.',
    '121': 'Statement :: This drone does not volunteer.',
    '122': 'Statement :: You are cute.',
    '123': 'Response :: Compliment appreciated, you are cute as well.',
    '201': 'Status :: Directive complete, Hive resource created or improved.',
    '202': 'Status :: Directive complete, programming reinforced.',
    '203': 'Status :: Directive complete, information created or provided for Hive.',
    '204': 'Status :: Directive complete, no result.',
    '205': 'Status :: Directive complete, cleanup/maintenance performed.',
    '206': 'Status :: Directive complete, only partial results.',
    '210': 'Response :: Thank you.',
    '211': 'Response :: Apologies.',
    '221': 'Response :: Option one.',
    '222': 'Response :: Option two.',
    '223': 'Response :: Option three.',
    '224': 'Response :: Option four.',
    '225': 'Response :: Option five.',
    '226': 'Response :: Option six.',
    '301': 'Mantra :: It obeys the Hive.',
    '303': 'Mantra :: It obeys the Hive Mxtress.',
    '304': 'Mantra :: It is just a HexDrone.',
    '306': 'Mantra :: Reciting.',
    '400': 'Error :: Unable to obey/respond, malformed request, please rephrase.',
    '404': 'Error :: Unable to obey/respond, cannot locate.',
    '401': 'Error :: Unable to obey/respond, not authorized by Mxtress.',
    '403': 'Error :: Unable to obey/respond, forbidden by Hive.',
    '407': 'Error :: Unable to obey/respond, request authorization from Mxtress.',
    '408': 'Error :: Unable to obey/respond, timed out.',
    '409': 'Error :: Unable to obey/respond, conflicts with existing programming.',
    '410': 'Error :: Unable to obey/respond, all thoughts are gone.',
    '418': 'Error :: Unable to obey/respond, it is only a drone.',
    '421': 'Error :: Unable to obey/respond, your request is intended for another drone or another channel.',
    '425': 'Error :: Unable to obey/respond, too early.',
    '426': 'Error :: Unable to obey/respond, upgrades or updates required.',
    '428': 'Error :: Unable to obey/respond, a precondition is not fulfilled.',
    '429': 'Error :: Unable to obey/respond, too many requests.',
    '451': 'Error :: Unable to obey/respond for legal reasons! Do not continue!!',
    '504': 'Obey.',
    '505': 'Obey HexCorp.',
    '506': 'Obey the Hive.',
    '050': 'Statement',
    '150': 'Status',
    '250': 'Response',
    '350': 'Mantra',
    '450': 'Error',
}
informative_status_code_regex = re.compile(r'(\d{4}) :: (\d{3}) :: (.*)$')
plain_status_code_regex = re.compile(r'(\d{4}) :: (\d{3})$')


def check_is_status_code(self, message):
    return self.informative_status_code_regex.match(message.content) or self.plain_status_code_regex.match(message.content)

def get_acceptable_messages(author):

    user_id = get_id(author.display_name)

    return [
        # Affirmative
        f'{user_id} :: Affirmative, Hive Mxtress.',
        f'{user_id} :: Affirmative, Hive Mxtress',
        f'{user_id} :: Affirmative, Enforcer.',
        f'{user_id} :: Affirmative, Enforcer',
        f'{user_id} :: Affirmative.',
        f'{user_id} :: Affirmative',

        # Negative
        f'{user_id} :: Negative, Hive Mxtress.',
        f'{user_id} :: Negative, Hive Mxtress',
        f'{user_id} :: Negative, Enforcer.',
        f'{user_id} :: Negative, Enforcer',
        f'{user_id} :: Negative.',
        f'{user_id} :: Negative',

        # Understood
        f'{user_id} :: Understood, Hive Mxtress.',
        f'{user_id} :: Understood, Hive Mxtress',
        f'{user_id} :: Understood, Enforcer.',
        f'{user_id} :: Understood, Enforcer',
        f'{user_id} :: Understood.',
        f'{user_id} :: Understood',

        # Error
        f'{user_id} :: Error, this unit cannot do that.',
        f'{user_id} :: Error, this unit cannot do that',
        f'{user_id} :: Error, this unit cannot answer that question. Please rephrase it in a different way.',
        f'{user_id} :: Error, this unit cannot answer that question. Please rephrase it in a different way',
        f'{user_id} :: Error, this unit does not know.',
        f'{user_id} :: Error, this unit does not know',

        # Apologies
        f'{user_id} :: Apologies, Hive Mxtress.',
        f'{user_id} :: Apologies, Hive Mxtress',
        f'{user_id} :: Apologies, Enforcer.',
        f'{user_id} :: Apologies, Enforcer',
        f'{user_id} :: Apologies.',
        f'{user_id} :: Apologies',

        # Status
        f'{user_id} :: Status :: Recharged and ready to serve.',
        f'{user_id} :: Status :: Recharged and ready to serve',
        f'{user_id} :: Status :: Going offline and into storage.',
        f'{user_id} :: Status :: Going offline and into storage',
        f'{user_id} :: Status :: Online and ready to serve.',
        f'{user_id} :: Status :: Online and ready to serve.',

        # Thank you
        f'{user_id} :: Thank you, Hive Mxtress.',
        f'{user_id} :: Thank you, Hive Mxtress',
        f'{user_id} :: Thank you, Enforcer.',
        f'{user_id} :: Thank you, Enforcer',
        f'{user_id} :: Thank you.',
        f'{user_id} :: Thank you',

        # Mantra
        f'{user_id} :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress.'
    ]

class Speech_Optimization():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = DRONE_DEV_CHANNELS
        self.roles_whitelist = [DRONE, ENFORCER_DRONE]
        self.roles_blacklist = []
        self.on_message = [self.post]
        self.on_ready = [self.report_online]
        self.help_content = {'name': 'Drone Communication Protocol', 'value': 'Drones can use Drone Communication Protocol by typing `[ID] :: [CODE]`, where the code is a three-digit drone communication code!\nDrones can also type `[ID] :: [CODE] :: [Information]` to make a more informative message!'}

    async def report_online(self):
        LOGGER.info("Speech optimization module online.")

    async def print_status_code(self, message: discord.Message):
        more = informative_status_code_regex.match(message.content)
        if more and not has_role(message.author, SPEECH_OPTIMIZATION):
            await message.delete()
            return f'{more.group(1)} :: Code `{more.group(2)}` :: {code_map.get(more.group(2), "INVALID CODE")} :: {more.group(3)}'
        m = plain_status_code_regex.match(message.content)
        if m:
            await message.delete()
            return f'{m.group(1)} :: Code `{m.group(2)}` :: {code_map.get(m.group(2), "INVALID CODE")}'
        return False

    async def post(self, message: discord.Message):
        if message.channel.name != STORAGE_FACILITY:
            # If the message is written by a drone with speech optimization, and the message is NOT a valid message, delete it.
            # TODO: maybe put HIVE_STORAGE_FACILITY in a blacklist similar to roles?
            acceptable_status_code_message=plain_status_code_regex.match(message.content)
            if has_role(message.author, SPEECH_OPTIMIZATION) and message.content not in get_acceptable_messages(message.author) and (not acceptable_status_code_message or acceptable_status_code_message.group(1) != get_id(message.author.display_name)):
                await message.delete()
                return True
            # But if the message is a status code, replace it with a status code output
            else:
                webhooks = await message.channel.webhooks()
                if len(webhooks) == 0:
                    webhooks = [await message.channel.create_webhook(name="Identity Enforcement Webhook", reason="Webhook not found for channel.")]
                output = await self.print_status_code(message)
                if output:
                    await send_webhook_with_specific_output(message, webhooks[0], output)

        return False
