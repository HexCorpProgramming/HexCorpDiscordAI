import logging
import re
import discord
from bot_utils import get_id
from channels import REPETITIONS, ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY
from ai.mantras import Mantra_Handler
from db.drone_dao import is_optimized, is_drone
from enum import Enum
from typing import Optional


class StatusType(Enum):
    NONE = 1
    # "Hello every(dr)one."

    PLAIN = 2
    # "5890 :: 200"

    INFORMATIVE = 3
    # "5890 :: 109 :: hdsjks"

    ADDRESS_BY_ID_PLAIN = 4
    # "5890 :: 110 :: 9813"

    ADDRESS_BY_ID_INFORMATIVE = 5
    # "5890 :: 110 :: 9813 :: You are cute!"

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

status_code_regex = re.compile(r'^((\d{4}) :: (\d{3}))( :: (.*))?$')
'''
Regex groups:
0: Full match. (5890 :: 200 :: Additional information)
1: Plain status code (5890 :: 200)
2: Author's drone ID (5890)
3: Status code (200)
4: Informative status addition with double colon formatting (" :: Additional information")
5: Informative status text. ("Additional information")
'''

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


def status_correctly_identified(author: discord.Author, plain_status=None, informative_status=None):
    '''
    Returns true if status begins with author's drone ID. Otherwise returns false.

    Author: 5890
    Message: '5890 :: 200'
    Returns: True
    Message: '9813 :: 200'
    Returns: False
    '''

    required_id = get_id(author.display_name)

    if plain_status is not None:
        return required_id == plain_status.group(1)
    elif informative_status is not None:
        return required_id == informative_status.group(1)
    else:
        # This shouldn't happen.
        return False


def translate_code(plain_status=None, informative_status=None, special_status=None):
    '''
    Gets the human-readble status and rewrites the message in full.

    Regex groups:
    (1): Author's drone ID.
    (2): Status code e.g "200"
    (3): Additional information (informative_status only).
    '''

    if plain_status:
        return f"{plain_status.group(2)} + this is a plain status code"
    elif informative_status:
        return f"{informative_status.group(2)} + this is an informative status code"
    else:
        return None


def get_status_type(status: Optional[re.Match]):
    if status is None:
        return StatusType.NONE
    elif status.group(3) == "110" and status.group(4) is None:
        return StatusType.ADDRESS_PLAIN
    elif status.group(3) == "110" and status.group(4) is not None:
        return StatusType.ADDRESS_INFORMATIVE
    elif status.group(4) is not None:
        return StatusType.INFORMATIVE
    else:
        return StatusType.PLAIN

async def optimize_speech(message: discord.Message, message_copy):
    '''
    This function allows status codes to be transformed into human-readable versions.
    "5890 :: 200" > "5890 :: Code 200 :: Affirmative"

    Drones can append additional information after a status code.
    Optimized drones cannot, and will have their message deleted if attempted.
    '''

    # Do not attempt to optimize non-drones.
    if not is_drone(message.author):
        return False

    # Attempt to find a status code message.
    status = status_code_regex.match(message_copy.content)

    # Determine type type
    status_type = get_status_type(status)

'''
TODO:

Rewrite the regex so there's only one status code regex.
`^((\d{4}) :: (\d{3}))( :: (.*)$)?`
This allows the first matched group to be a plain status code.
So just check if .group(1) == message.content
If true, then the user has posted a plain status code
Otherwise, the user has posted an informative status code.

Given the message:
5890 :: 110 :: Hello world

0: 5890 :: 110 :: Hello world (Full match)
1: 5890 :: 110 (Plain status code)
2: 5890 (Drone ID)
3: 110 (Status code)
4:  :: Hello world (Informational status full formatting)
5: Hello world (Informational status message)
'''