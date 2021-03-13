import logging
import re
import discord
from bot_utils import get_id
from db.drone_dao import is_drone
from resources import code_map
from enum import Enum


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

status_code_regex = re.compile(r'^((\d{4}) :: (\d{3}))( :: (.*))?$', re.DOTALL)
'''
Regex groups for full status code regex:
0: Full match. (5890 :: 200 :: Additional information)
1: Plain status code (5890 :: 200)
2: Author's drone ID (5890)
3: Status code (200)
4: Informative status addition with double colon (" :: Additional information")
5: Informative status text. ("Additional information")
'''

address_by_id_regex = re.compile(r'(\d{4})( :: (.*))?', re.DOTALL)
'''
This regex is to be checked on the status regex's 5th group when the status code is 110 (addressing).
0: Full match ("9813 :: Additional information")
1: ID of drone to address ("9813")
2: Informative status text with double colon (" :: Additional information")
3: Informative status text ("Additional information")
'''


def get_status_type(message: str):

    code_match = status_code_regex.match(message)

    if code_match is None:
        return (StatusType.NONE, None, None)

    # Special case handling for addressing by ID.
    if code_match.group(3) == "110" and code_match.group(5) is not None:
        address_match = address_by_id_regex.match(code_match.group(5))
        if address_match is None:
            return (StatusType.INFORMATIVE, code_match, None)
        elif address_match.group(2) is not None:
            return (StatusType.ADDRESS_BY_ID_INFORMATIVE, code_match, address_match)
        else:
            return (StatusType.ADDRESS_BY_ID_PLAIN, code_match, address_match)

    elif code_match.group(4) is not None:
        return (StatusType.INFORMATIVE, code_match, None)
    else:
        return (StatusType.PLAIN, code_match, None)


def build_status_message(status_type, code_match, address_match):

    base_message = f"{code_match.group(2)} :: Code `{code_match.group(3)}` :: "

    if status_type == StatusType.PLAIN:
        return f"{base_message}{code_map.get(code_match.group(3), 'INVALID CODE')}"
    elif status_type == StatusType.INFORMATIVE:
        return f"{base_message}{code_map.get(code_match.group(3), 'INVALID CODE')}{code_match.group(4)}"
    elif status_type == StatusType.ADDRESS_BY_ID_PLAIN:
        return f"{base_message}Addressing: Drone #{address_match.group(1)}"
    elif status_type == StatusType.ADDRESS_BY_ID_INFORMATIVE:
        return f"{base_message}Addressing: Drone #{address_match.group(1)}{address_match.group(2)}"


async def optimize_speech(message: discord.Message, message_copy):
    '''
    This function allows status codes to be transformed into human-readable versions.
    "5890 :: 200" > "5890 :: Code 200 :: Affirmative"

    This function assumes message validity has already been assessed by speech_optimization_enforcement.
    '''

    # Do not attempt to optimize non-drones.
    if not is_drone(message.author):
        return False

    # Determine message type
    status_type, code_match, address_match = get_status_type(message_copy.content)

    if status_type == StatusType.NONE:
        return False

    # Confirm the status starts with the drone's ID
    if code_match.group(2) != get_id(message.author.display_name):
        LOGGER.info("Status did not match drone ID.")
        await message.delete()
        return True

    # Build message based on status type.
    message_copy.content = build_status_message(status_type, code_match, address_match)

    return False
