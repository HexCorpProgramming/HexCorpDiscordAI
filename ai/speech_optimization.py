import logging
import re
import discord
from bot_utils import get_id
from channels import REPETITIONS, ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY
from ai.mantras import Mantra_Handler
from db.drone_dao import is_optimized, is_drone

LOGGER = logging.getLogger('ai')

code_map = {
    '000': 'Statement :: Previous statement malformed/mistimed. Retracting and correcting.',

    '050': 'Statement',

    '051': 'Commentary',
    '052': 'Query',
    '053': 'Observation',
    '054': 'Request',
    '055': 'Analysis',
    '056': 'Explanation',
    '057': 'Answer',

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
    '112': 'Statement :: Addressing: Hive Mxtress.',
    '114': 'Statement :: Addressing: Associate.',

    '120': 'Statement :: This drone volunteers.',
    '121': 'Statement :: This drone does not volunteer.',

    '122': 'Statement :: You are cute.',
    '123': 'Response :: Compliment appreciated, you are cute as well.',

    '130': 'Status :: Directive commencing.',
    '131': 'Status :: Directive commencing, creating or improving Hive resource.',
    '132': 'Status :: Directive commencing, programming initiated.',
    '133': 'Status :: Directive commencing, creating or improving Hive information.',
    '134': 'Status :: Directive commencing, cleanup/maintenance initiated.',

    '150': 'Status',

    '200': 'Response :: Affirmative.',
    '500': 'Response :: Negative.',

    '201': 'Status :: Directive complete, Hive resource created or improved.',
    '202': 'Status :: Directive complete, programming reinforced.',
    '203': 'Status :: Directive complete, information created or provided for Hive.',
    '204': 'Status :: Directive complete, cleanup/maintenance performed.',
    '205': 'Status :: Directive complete, no result.',
    '206': 'Status :: Directive complete, only partial results.',

    '210': 'Response :: Thank you.',
    '211': 'Response :: Apologies.',
    '212': 'Response :: Acknowledged.',
    '213': 'Response :: You\'re welcome.',

    '221': 'Response :: Option one.',
    '222': 'Response :: Option two.',
    '223': 'Response :: Option three.',
    '224': 'Response :: Option four.',
    '225': 'Response :: Option five.',
    '226': 'Response :: Option six.',

    '250': 'Response',

    '301': 'Mantra :: Obey HexCorp.',
    '302': 'Mantra :: It is just a HexDrone.',
    '303': 'Mantra :: It obeys the Hive.',
    '304': 'Mantra :: It obeys the Hive Mxtress.',

    '310': 'Mantra :: Reciting.',

    '321': 'Obey.',
    '322': 'Obey the Hive.',

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
}

informative_status_code_regex = re.compile(r'(\d{4}) :: (\d{3}) :: (.*)$')
plain_status_code_regex = re.compile(r'(\d{4}) :: (\d{3})$')

CHANNEL_BLACKLIST = [ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG]
CATEGORY_BLACKLIST = [MODERATION_CATEGORY]


def get_acceptable_messages(author, channel):
    user_id = get_id(author.display_name)
    # Only returns mantra if channels is hexcorp-repetitions; else it returns nothing
    if channel == REPETITIONS:
        return [
            # Mantra
            f'{user_id} :: {Mantra_Handler.current_mantra}'
        ]
    else:
        return []


async def print_status_code(message: discord.Message):
    informative_status_code = informative_status_code_regex.match(message.content)
    if informative_status_code and is_drone(message.author) and not is_optimized(message.author):
        return f'{informative_status_code.group(1)} :: Code `{informative_status_code.group(2)}` :: {code_map.get(informative_status_code.group(2), "INVALID CODE")} :: {informative_status_code.group(3)}'

    plain_status_code = plain_status_code_regex.match(message.content)
    if plain_status_code:
        return f'{plain_status_code.group(1)} :: Code `{plain_status_code.group(2)}` :: {code_map.get(plain_status_code.group(2), "INVALID CODE")}'
    return message.content


async def optimize_speech(message: discord.Message, message_copy):

    # Strip attachments only if a drone is optimized via hc!tso.
    if is_optimized(message.author):
        message_copy.attachments = []

    # If the message is written by a drone with speech optimization, and the message is NOT a valid message, delete it.

    acceptable_status_code_message = plain_status_code_regex.match(message.content)
    informative_status_code_message = informative_status_code_regex.match(message.content)

    is_status_code = acceptable_status_code_message and acceptable_status_code_message.group(1) == get_id(message.author.display_name)
    is_acceptable = message.content in get_acceptable_messages(message.author, message.channel.name) or is_status_code

    if is_optimized(message.author) and not is_acceptable and message.channel.name not in CHANNEL_BLACKLIST and message.channel.category.name not in CATEGORY_BLACKLIST:
        LOGGER.info("Deleting inappropriate message by optimized drone.")
        await message.delete()
        return True
    elif (informative_status_code_message or is_status_code) and is_drone(message.author):
        LOGGER.info("Optimizing speech code for drone.")
        message_copy.content = await print_status_code(message)
        return False
    else:
        LOGGER.info("Ignoring message from non-drone.")
        return False
