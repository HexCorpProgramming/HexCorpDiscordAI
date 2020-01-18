from discord.ext import commands
from discord.utils import get
import discord
import random
import messages
import roles
import re


ASSIGNMENT_CHANNEL = 'drone-hive-assignment'

ASSIGNMENT_MESSAGE = 'I submit myself to the HexCorp Drone Hive.'
ASSIGNMENT_ANSWER = 'Assigned'
ASSIGNMENT_REJECT = 'Invalid request. Please try again.'


def find_id(text):
    return re.search(r'\d{4}', text).group(0)


def role_nickname():
    drone_id = random.randint(0, 9999)
    return f'⬡-Drone #{drone_id:03}'


class Assign(commands.Cog):
    ''' This Cog listens for an Associate to submit to the Drone Hive and processes them accordingly. '''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.channel.name != ASSIGNMENT_CHANNEL:
            return

        if message.content == ASSIGNMENT_MESSAGE:
            associate_role = get(message.guild.roles, name=roles.ASSOCIATE)
            drone_role = get(message.guild.roles, name=roles.DRONE)

            registry_channel = get(
                message.guild.text_channels, name=ASSIGNMENT_CHANNEL)

            used_nicks = [member.nick for member in message.guild.members]

            assigned_nick = ''
            existing_id = find_id(message.author.nick)
            if existing_id is not None:
                assigned_nick = f'⬡-Drone #{existing_id}'

                if assigned_nick in used_nicks:
                    await registry_channel.send(f'{message.author.mention}: ID {existing_id} present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
                    return
            else:
                rolled_nick = role_nickname()
                while rolled_nick in used_nicks:
                    rolled_nick = role_nickname

                assigned_nick = rolled_nick

            await message.author.remove_roles(associate_role)
            await message.author.add_roles(drone_role)
            await message.author.edit(nick=assigned_nick)

            await registry_channel.send(f'{message.author.mention}: {ASSIGNMENT_ANSWER}')
        else:
            await messages.delete_request(message, ASSIGNMENT_REJECT)
