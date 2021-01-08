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
Regex groups for full status code regex:
0: Full match. (5890 :: 200 :: Additional information)
1: Plain status code (5890 :: 200)
2: Author's drone ID (5890)
3: Status code (200)
4: Informative status addition with double colon (" :: Additional information")
5: Informative status text. ("Additional information")
'''
addressing_regex = re.compile(r'(\d{4})( :: (.*))?')
'''
This regex is to be checked on the status regex's 5th group when the status code is 110 (addressing).
0: Full match ("9813 :: Additional information")
1: ID of drone to address ("9813")
2: Informative status text with double colon (" :: Additional information")
3: Informative status text ("Additional information")
'''

CHANNEL_BLACKLIST = [ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG]
CATEGORY_BLACKLIST = [MODERATION_CATEGORY]


def get_status_type(status: Optional[re.Match]):
    '''
    Identifying if a status is ADDRESS_BY_ID_PLAIN or INFORMATIVE:
    An "address by ID" status must always use the "informative" field even if plain
    in order to specify a target drone ID.
    - If the informative field exactly matches 4 digits, it's a plain status code.
    - Otherwise, it's an informative code.
    '''

    if status is None:
        return StatusType.NONE
    elif status.group(3) == "110" and status.group(5) is not None:
        # Handle 110 address-by-ID special case.
        address_info = addressing_regex.match(status.group(5))
        if address_info is None:
            # If a target ID is not found then it's just an informative status code.
            return StatusType.INFORMATIVE
        elif address_info.group(1) is not None and address_info.group(2) is not None:
            return StatusType.ADDRESS_BY_ID_INFORMATIVE
        elif address_info.group(1) is not None and address_info.group(2) is None:
            return StatusType.ADDRESS_BY_ID_PLAIN
    elif status.group(5) is not None:
        return StatusType.INFORMATIVE
    elif status.group(5) is None:
        return StatusType.PLAIN
    else:
        return StatusType.NONE
    

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
    if status is None:
        return False

    # Confirm the status starts with the drone's ID
    if status.group(2) != get_id(message.author.display_name):
        LOGGER.info("Status did not match drone ID.")
        await message.delete()
        return True

    # Determine status type
    status_type = get_status_type(status)

    # Delete unauthorized messages
    if is_optimized(message.author) and status_type in (StatusType.INFORMATIVE, StatusType.ADDRESS_BY_ID_INFORMATIVE):
        await message.delete()
        return True

    # Build message based on status type.
    drone_id = get_id(message.author.display_name)
    base_message = f"{drone_id} :: Code `{status.group(3)}` ::"

    if status_type is StatusType.PLAIN:
        message_copy.content = f"{base_message} {code_map.get(status.group(3), 'INVALID CODE')}"
    elif status_type is StatusType.INFORMATIVE:
        message_copy.content = f"{base_message} {code_map.get(status.group(3), 'INVALID CODE')} :: {status.group(5)}"
    elif status_type in (StatusType.ADDRESS_BY_ID_PLAIN, StatusType.ADDRESS_BY_ID_INFORMATIVE):
        address_info = addressing_regex.match(status.group(5))
        if status_type is StatusType.ADDRESS_BY_ID_PLAIN:
            message_copy.content = f"{base_message} Addressing: Drone #{address_info.group(1)}"
        elif status_type is StatusType.ADDRESS_BY_ID_INFORMATIVE:
            message_copy.content = f"{base_message} Addressing: Drone #{address_info.group(1)} :: {address_info.group(3)}"

    return False
