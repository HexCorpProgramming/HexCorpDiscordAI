from discord.ext import commands
from discord.utils import get
from typing import List
import discord
import random
import messages
import roles
import re
from channels import ASSIGNMENT_CHANNEL

ASSIGNMENT_MESSAGE = 'I submit myself to the HexCorp Drone Hive.'
ASSIGNMENT_ANSWER = 'Assigned'
ASSIGNMENT_REJECT = 'Invalid request. Please try again.'

RESERVED_IDS = ['0006', '0000', '0001', '0002', '0003', '0004', '0005', '6969', '0420', '3141']


def find_id(text: str) -> str:
    match = re.search(r'\d{4}', text)
    if match is not None:
        return match.group(0)
    else:
        return None


def roll_id() -> str:
    id = random.randint(0, 9999)
    return f'{id:03}'


def invalid_ids(members: List[discord.Member], relevant_roles: List[discord.Role]) -> List[str]:
    relevant_ids = []
    for member in members:
        is_relevant_role = [(role in relevant_roles) for role in member.roles]
        member_id = find_id(member.display_name)
        if any(is_relevant_role) and member_id is not None:
            relevant_ids.append(member_id)

    return relevant_ids + RESERVED_IDS


class Assign(commands.Cog):
    ''' This Cog listens for an Associate to submit to the Drone Hive and processes them accordingly. '''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.channel.name != ASSIGNMENT_CHANNEL: # message from bot or not in correct channel return
            return

        #if the message is correct for being added, yay! if not, delete the message and let them know its bad
        if message.content == ASSIGNMENT_MESSAGE:
            associate_role = get(message.guild.roles, name=roles.ASSOCIATE)
            drone_role = get(message.guild.roles, name=roles.DRONE)

            assigned_nick = ''
            used_ids = invalid_ids(message.guild.members, [drone_role])
            existing_id = find_id(message.author.display_name) # does user have a drone id in their display name?
            if existing_id is not None: 
                if existing_id in used_ids: # make sure display name number doesnt conflict
                    await message.channel.send(f'{message.author.mention}: ID {existing_id} present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
                    return
                # if no conflict, assign nickname
                assigned_nick = f'⬡-Drone #{existing_id}'
            else:
                rolled_id = roll_id()
                while rolled_id in used_ids: # loop until no conflict
                    rolled_id = roll_id()
                # when no conflict, assign nickname
                assigned_nick = f'⬡-Drone #{rolled_id}'
            

            # give them the drone role
            await message.author.remove_roles(associate_role)
            await message.author.add_roles(drone_role)
            await message.author.edit(nick=assigned_nick)

            await message.channel.send(f'{message.author.mention}: {ASSIGNMENT_ANSWER}')
        else:
            await messages.delete_request(message, ASSIGNMENT_REJECT)
