import random
from datetime import datetime

import discord
from discord.utils import get

import messages
import roles
from channels import ASSIGNMENT_CHANNEL
from db.drone_dao import insert_drone, get_used_drone_ids
from db.data_objects import Drone
from bot_utils import get_id

ASSIGNMENT_MESSAGE = 'I submit myself to the HexCorp Drone Hive.'
ASSIGNMENT_ANSWER = 'Assigned.'
ASSIGNMENT_REJECT = 'Invalid request. Please try again.'

RESERVED_IDS = ['0006', '0000', '0001', '0002', '0003', '0004', '0005', '6969', '0420', '4200', '3141', '0710', '7100', '1488']


def roll_id() -> str:
    id = random.randint(0, 9999)
    return f'{id:04}'


async def check_for_assignment_message(message: discord.Message):

    if message.channel.name != ASSIGNMENT_CHANNEL:
        return False

    # if the message is correct for being added, yay! if not, delete the message and let them know its bad
    if message.content == ASSIGNMENT_MESSAGE:
        associate_role = get(message.guild.roles, name=roles.ASSOCIATE)
        drone_role = get(message.guild.roles, name=roles.DRONE)

        assigned_nick = ''
        used_ids = get_used_drone_ids() + RESERVED_IDS
        assigned_id = get_id(message.author.display_name)  # does user have a drone id in their display name?
        if assigned_id is not None:
            if assigned_id in used_ids:  # make sure display name number doesnt conflict
                await message.channel.send(f'{message.author.mention}: ID {assigned_id} present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
                return True
        else:
            assigned_id = roll_id()
            while assigned_id in used_ids:  # loop until no conflict
                assigned_id = roll_id()

        assigned_nick = f'⬡-Drone #{assigned_id}'

        # give them the drone role
        await message.author.remove_roles(associate_role)
        await message.author.add_roles(drone_role)
        await message.author.edit(nick=assigned_nick)

        # add new drone to DB
        new_drone = Drone(message.author.id, assigned_id, False, False, "", datetime.now())
        insert_drone(new_drone)

        await message.channel.send(f'{message.author.mention}: {ASSIGNMENT_ANSWER}')
    else:
        await messages.delete_request(message, ASSIGNMENT_REJECT)

    return True
