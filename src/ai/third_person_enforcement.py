import re
import logging
from discord import Message
from src.ai.data_objects import MessageCopy
from src.drone_member import DroneMember

LOGGER = logging.getLogger('ai')


async def enforce_third_person(message: Message, message_copy: MessageCopy) -> None:
    '''
    Replace first person pronounds if third person enforcement is enabled.
    '''

    member = await DroneMember.create(message.author)

    if member.drone and member.drone.third_person_enforcable(message.channel):
        message_copy.third_person_enforced = True
        message_copy.content = replace_third_person(message_copy.content)


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
