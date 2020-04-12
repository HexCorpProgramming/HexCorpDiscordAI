from discord.ext import commands
from discord.utils import get
import discord
import messages
from roles import HIVE_MXTRESS, DRONE_MODE, has_role
from channels import HIVE_STORAGE_FACILITY, EVERYWHERE
import re


def get_acceptable_messages(author):

    user_id = get_user_id(author.display_name)

    return [
        # Affirmative
        user_id + ' :: Affirmative, Hive Mxtress.',
        user_id + ' :: Affirmative, Hive Mxtress',
        user_id + ' :: Affirmative, Enforcer.',
        user_id + ' :: Affirmative, Enforcer',
        user_id + ' :: Affirmative.',
        user_id + ' :: Affirmative',

        # Negative
        user_id + ' :: Negative, Hive Mxtress.',
        user_id + ' :: Negative, Hive Mxtress',
        user_id + ' :: Negative, Enforcer.',
        user_id + ' :: Negative, Enforcer',
        user_id + ' :: Negative.',
        user_id + ' :: Negative',

        # Understood
        user_id + ' :: Understood, Hive Mxtress.',
        user_id + ' :: Understood, Hive Mxtress',
        user_id + ' :: Understood, Enforcer.',
        user_id + ' :: Understood, Enforcer',
        user_id + ' :: Understood.',
        user_id + ' :: Understood',

        # Error
        user_id + ' :: Error, this unit cannot do that.',
        user_id + ' :: Error, this unit cannot do that',
        user_id + ' :: Error, this unit cannot answer that question. Please rephrase it in a different way.',
        user_id + ' :: Error, this unit cannot answer that question. Please rephrase it in a different way',
        user_id + ' :: Error, this unit does not know.',
        user_id + ' :: Error, this unit does not know',

        # Apologies
        user_id + ' :: Apologies, Hive Mxtress.',
        user_id + ' :: Apologies, Hive Mxtress',
        user_id + ' :: Apologies, Enforcer.',
        user_id + ' :: Apologies, Enforcer',
        user_id + ' :: Apologies.',
        user_id + ' :: Apologies',

        # Status
        user_id + ' :: Status :: Recharged and ready to serve.',
        user_id + ' :: Status :: Recharged and ready to serve',
        user_id + ' :: Status :: Going offline and into storage.',
        user_id + ' :: Status :: Going offline and into storage',
        user_id + ' :: Status :: Online and ready to serve.',
        user_id + ' :: Status :: Online and ready to serve.',

        # Thank you
        user_id + ' :: Thank you, Hive Mxtress.',
        user_id + ' :: Thank you, Hive Mxtress',
        user_id + ' :: Thank you, Enforcer.',
        user_id + ' :: Thank you, Enforcer',
        user_id + ' :: Thank you.',
        user_id + ' :: Thank you',

        # Mantra
        user_id + ' :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress.'
    ]


def get_user_id(username):
    drone_id = re.search(r"\d{4}", username).group()
    return drone_id if drone_id is not None else 0000


class Drone_Mode():

    def __init__(self, bot):
        self.bot = bot
        self.channels = [EVERYWHERE]
        self.roles_whitelist = [DRONE_MODE]
        self.roles_blacklist = []
        self.on_message = [self.post]
        self.on_ready = [self.report_online]

    async def report_online(self):
        print("Drone mode module online.")

    async def post(self, message: discord.Message):
        # If the message is written by a drone mode drone, and the message is NOT a valid message, delete it.
        # TODO: maybe put HIVE_STORAGE_FACILITY in a blacklist similar to roles?
        if message.channel.name != HIVE_STORAGE_FACILITY:
            if message.content not in get_acceptable_messages(message.author):
                await message.delete()
                return True

        return False
