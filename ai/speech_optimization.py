import logging
import re
import discord
from bot_utils import get_id
from channels import REPETITIONS, ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY
from db.drone_dao import is_optimized, is_drone
from resources import code_map
from enum import Enum
from typing import Optional
from ai.mantras import Mantra_Handler


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


def should_not_optimize(message):
    '''
    Handles cases where the speech optimizer receieves a message it should not optimize.

    Returns true if:
    - Channel is mantras and message is current mantra.
    - Message from any channel: Orders reporting, Orders completion, Moderation channel, moderation log.
    - Message from category: Moderation
    '''

    drone_id = get_id(message.author.display_name)
    acceptable_mantra = f"{drone_id} :: {Mantra_Handler.current_mantra}"

    return any([
        (message.channel.name == REPETITIONS and message.content == acceptable_mantra),
        (message.channel.name in (ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG)),
        (message.channel.category.name == MODERATION_CATEGORY)
    ])


def build_status_message(status_type, status, drone_id):

    base_message = f"{drone_id} :: Code `{status.group(3)}` ::"

    if status_type is StatusType.PLAIN:
        return f"{base_message} {code_map.get(status.group(3), 'INVALID CODE')}"
    elif status_type is StatusType.INFORMATIVE:
        return f"{base_message} {code_map.get(status.group(3), 'INVALID CODE')} :: {status.group(5)}"
    elif status_type in (StatusType.ADDRESS_BY_ID_PLAIN, StatusType.ADDRESS_BY_ID_INFORMATIVE):
        address_info = addressing_regex.match(status.group(5))
        if status_type is StatusType.ADDRESS_BY_ID_PLAIN:
            return f"{base_message} Addressing: Drone #{address_info.group(1)}"
        elif status_type is StatusType.ADDRESS_BY_ID_INFORMATIVE:
            return f"{base_message} Addressing: Drone #{address_info.group(1)} :: {address_info.group(3)}"
    else:
        return None


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

    # Skip edge cases
    if should_not_optimize(message):
        return False

    # Attempt to find a status code message.
    status = status_code_regex.match(message_copy.content)
    if status is None and is_optimized(message.author):
        await message.delete()
        return True

    # Confirm the status starts with the drone's ID
    if status.group(2) != get_id(message.author.display_name):
        LOGGER.info("Status did not match drone ID.")
        await message.delete()
        return True

    # Determine status type
    status_type = get_status_type(status)

    # Delete unauthorized messages
    if is_optimized(message.author) and status_type in (StatusType.INFORMATIVE, StatusType.ADDRESS_BY_ID_INFORMATIVE):
        LOGGER.info("Deleting unauthorized message from optimized HexDrone.")
        await message.delete()
        return True
    else:
        LOGGER.info("Message is acceptable.")

    # Build message based on status type.
    drone_id = get_id(message.author.display_name)

    if (final_message := build_status_message(status=status, status_type=status_type, drone_id=drone_id)) is not None:
        message_copy.content = final_message

    return False
