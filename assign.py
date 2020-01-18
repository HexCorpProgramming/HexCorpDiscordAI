from discord.ext import commands
from discord.utils import get
import discord
import random
import messages
import roles


ASSIGNMENT_CHANNEL = 'drone-hive-assignment'

ASSIGNMENT_MESSAGE = 'I submit myself to the HexCorp Drone Hive.'
ASSIGNMENT_ANSWER = 'Assigned'
ASSIGNMENT_REJECT = 'Invalid request. Please try again.'


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

            await message.author.remove_roles(associate_role)
            await message.author.add_roles(drone_role)

            registry_channel = get(
                message.guild.text_channels, name=ASSIGNMENT_CHANNEL)

            used_nicks = [member.nick for member in message.guild.members]
            rolled_nick = role_nickname()
            while rolled_nick in used_nicks:
                rolled_nick = role_nickname

            await message.author.edit(nick=rolled_nick)
            await registry_channel.send(f'{message.author.mention}: {ASSIGNMENT_ANSWER}')
        else:
            await messages.delete_request(message, ASSIGNMENT_REJECT)
