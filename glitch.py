import discord
import random
from roles import GLITCHED, has_role
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

def glitch_if_applicable(text: str, author: discord.Member):
    if has_role(author, GLITCHED):
        template_match = glitch_template.match(text)
        if template_match:
            return template_match.group(1) + glitch(template_match.group(2))
        else:
            return glitch(text)
    else:
        return text