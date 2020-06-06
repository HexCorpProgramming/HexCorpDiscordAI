import random

# usage:
# python glitch.py

combining_characters = range(0x0300, 0x036F)

def glitch(text: str):
    glitched_text = ""

    for c in text:
        glitched_text += c
        for _ in range(0, random.randint(0, 10)):
            glitched_text += chr(random.choice(combining_characters))

    return glitched_text

print(glitch('9813 is a good drone.'))
