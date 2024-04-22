import discord

from src.ai.data_objects import MessageCopy
from src.db.data_objects import Drone


async def enforce_identity(message: discord.Message, message_copy: MessageCopy):
    '''
    Message listener for activating identity enforcement.
    '''

    drone = Drone.find(discord_id=message.author.id)

    if drone and drone.identity_enforcable(message.channel):
        message_copy.identity_enforced = True
