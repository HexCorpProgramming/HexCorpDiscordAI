import discord
import random
from db.drone_dao import is_glitched
import re

combining_characters = list(range(0x0300, 0x036F))


def glitch(text: str):
    glitched_text = ""

    for c in text:
        glitched_text += c
        for _ in range(0, random.randint(0, 20)):
            glitched_text += chr(random.choice(combining_characters))

    return glitched_text


glitch_template = re.compile(r'(\d{4} :: )(.*)')


async def glitch_if_applicable(message: discord.Message, message_copy):
    if is_glitched(message.author):
        template_match = glitch_template.match(message_copy.content)
        if template_match:
            message_copy.content = template_match.group(1) + glitch(template_match.group(2))  # If a drone is using an op code, only glitch the part after its ID.
        else:
            message_copy.content = glitch(message_copy.content)  # Otherwise, glitch the whole message.
    return False
