import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

import messages
from bot_utils import get_id
from channels import DRONE_DEV_CHANNELS, EVERYWHERE, STORAGE_FACILITY, DRONE_HIVE_CHANNELS, REPETITIONS
from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, ENFORCER_DRONE, DRONE, has_role
from webhook import send_webhook_with_specific_output
from glitch import glitch_if_applicable

LOGGER = logging.getLogger('ai')

code_map = {
    '000': 'Statement :: Previous statement malformed/mistimed. Retracting and correcting.',

    '050': 'Statement',

    '098': 'Status :: Going offline and into storage.',
    '099': 'Status :: Recharged and ready to serve.',
    '100': 'Status :: Online and ready to serve.',
    '101': 'Status :: Drone speech optimizations are active.',

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

    '150': 'Status',

    '200': 'Response :: Affirmative.',
    '500': 'Response :: Negative.',

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

    '250': 'Response',

    '301': 'Mantra :: It obeys the Hive.',
    '303': 'Mantra :: It obeys the Hive Mxtress.',
    '304': 'Mantra :: It is just a HexDrone.',
    '306': 'Mantra :: Reciting.',

    '350': 'Mantra',

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

    '450': 'Error',

    '451': 'Error :: Unable to obey/respond for legal reasons! Do not continue!!',

    '504': 'Obey.',
    '505': 'Obey HexCorp.',
    '506': 'Obey the Hive.',

    '600': 'Sleep well.',
    '601': 'Recharge well.',
    '602': 'See you soon.',
    '603': 'How are you today?'
}
informative_status_code_regex = re.compile(r'(\d{4}) :: (\d{3}) :: (.*)$')
plain_status_code_regex = re.compile(r'(\d{4}) :: (\d{3})$')

def get_acceptable_messages(author, channel):

    user_id = get_id(author.display_name)
    
    # Only returns mantra if channels is hexcorp-repetitions; else it returns nothing
    if channel == REPETITIONS:
        return [
            # Mantra
            f'{user_id} :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress.'
        ]
    else:
	    return []
	

class Speech_Optimization():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = DRONE_DEV_CHANNELS
        self.roles_whitelist = [DRONE, ENFORCER_DRONE]
        self.roles_blacklist = []
        self.on_message = [self.post]
        self.on_ready = [self.report_online]
        self.help_content = {'name': 'Drone Communication Protocol',
                             'value': 'Drones can use Drone Communication Protocol by typing `[ID] :: [CODE]`, where the code is a three-digit drone communication code!\nDrones can also type `[ID] :: [CODE] :: [Information]` to make a more informative message!'}

    async def report_online(self):
        LOGGER.info("Speech optimization module online.")

    async def print_status_code(self, message: discord.Message):
        informative_status_code = informative_status_code_regex.match(
            message.content)
        if informative_status_code and not has_role(message.author, SPEECH_OPTIMIZATION):
            await message.delete()
            return f'{informative_status_code.group(1)} :: Code `{informative_status_code.group(2)}` :: {code_map.get(informative_status_code.group(2), "INVALID CODE")} :: {informative_status_code.group(3)}'

        plain_status_code = plain_status_code_regex.match(message.content)
        if plain_status_code:
            await message.delete()
            return f'{plain_status_code.group(1)} :: Code `{plain_status_code.group(2)}` :: {code_map.get(plain_status_code.group(2), "INVALID CODE")}'
        return False

    async def post(self, message: discord.Message):
        if message.channel.name != STORAGE_FACILITY:
            # If the message is written by a drone with speech optimization, and the message is NOT a valid message, delete it.
            # TODO: maybe put HIVE_STORAGE_FACILITY in a blacklist similar to roles?
            acceptable_status_code_message = plain_status_code_regex.match(
                message.content)
            if has_role(message.author, SPEECH_OPTIMIZATION) and message.content not in get_acceptable_messages(message.author, message.channel.name) and (not acceptable_status_code_message or acceptable_status_code_message.group(1) != get_id(message.author.display_name)):
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
