import re
import logging
from discord import Member, Message
from src.ai.data_objects import MessageCopy
from src.channels import DRONE_HIVE_CHANNELS, HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY
from src.db.drone_dao import is_drone, is_third_person_enforced

LOGGER = logging.getLogger('ai')


async def enforce_third_person(message: Message, message_copy: MessageCopy) -> None:
    '''
    Replace first person pronounds if third person enforcement is enabled.
    '''

    if await third_person_enforcable(message.author, channel=message.channel):
        message_copy.third_person_enforced = True
        message_copy.content = replace_third_person(message_copy.content)


async def third_person_enforcable(member: Member, channel=None) -> bool:
    '''
    Takes a context or channel object and uses it to check if the identity of a user should be enforced.
    '''

    if channel is None:
        raise ValueError("identity_enforceable must be provided a context or channel object.")

    return await is_drone(member) and (channel.name in DRONE_HIVE_CHANNELS or await is_third_person_enforced(member)) and channel.category.name not in [HEXCORP_CONTROL_TOWER_CATEGORY, MODERATION_CATEGORY]


def replace_third_person(text: str) -> str:
    '''
    Replace first person pronouns with third person.
    '''

    # Replace "I've" at the beginning of a sentence with "It's".
    text = re.sub(r'(([.!?]|^)\s*)[iI]\'ve(\s|\W)', '\\1It\'s\\3', text)

    # Replace I, I'm, I'd, I'll at the beginning of a sentence with 'It'*'.
    text = re.sub('(([.!?]|^)\\s*)[iI](\'m|\'d|\'ll)?(?=\\s|\\W|$)', r'\1It\3', text)

    # Replace remaining first person pronouns.
    replacements = [
        ('I\'m', 'it\'s'),
        ('i\'m', 'it\'s'),
        ('I\'d', 'it\'d'),
        ('i\'d', 'it\'d'),
        ('I\'ll', 'it\'ll'),
        ('i\'ll', 'it\'ll'),
        ('I\'ve', 'it\'s'),
        ('i\'ve', 'it\'s'),
        ('I', 'it'),
        ('i', 'it'),
        ('Me', 'It'),
        ('me', 'it'),
        ('Am', 'Is'),
        ('am', 'is'),
        ('Mine', 'Its'),
        ('mine', 'its'),
        ('My', 'Its'),
        ('my', 'its'),
        ('Myself', 'Itself'),
        ('myself', 'itself'),
    ]

    for search, replace in replacements:
        text = re.sub(r'(\W|^)' + re.escape(search) + r'(\W|$)', r'\1' + replace + r'\2', text)

    return text
