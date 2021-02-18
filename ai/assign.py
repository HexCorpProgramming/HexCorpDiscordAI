import random
from datetime import datetime, timedelta
from typing import Optional, List

import discord
from discord.utils import get

import messages
import roles
from channels import ASSIGNMENT_CHANNEL
from db.drone_dao import insert_drone, get_used_drone_ids
from db.data_objects import Drone
from bot_utils import get_id
from resources import HIVE_MXTRESS_USER_ID

ASSIGNMENT_MESSAGE = 'I submit myself to the HexCorp Drone Hive.'
ASSIGNMENT_ANSWER = 'Assigned.'
ASSIGNMENT_REJECT = 'Invalid request. Please try again.'

RESERVED_IDS = ['0006', '0000', '0001', '0002', '0003', '0004', '0005', '6969', '0420', '4200', '3141', '0710', '7100', '1488']


def roll_id() -> str:
    id = random.randint(0, 9999)
    return f'{id:04}'


async def check_for_assignment_message(message: discord.Message, message_copy=None):

    if message.channel.name != ASSIGNMENT_CHANNEL:
        return False

    # member has not been on the server for the required period
    if message.author.joined_at > datetime.now() - timedelta(hours=24):
        await message.channel.send("Invalid request, associate must have existed on the server for at least 24 hours before dronification.")
        return False

    # if the message is correct for being added, yay! if not, delete the message and let them know its bad
    if message.content == ASSIGNMENT_MESSAGE:
        await create_drone(message.guild, message.author, message.channel)
    else:
        await messages.delete_request(message, ASSIGNMENT_REJECT)

    return True


async def create_drone(guild: discord.Guild,
                       target: discord.Member,
                       feedback_channel: discord.TextChannel,
                       additional_trusted_users: Optional[List[str]] = None,
                       temporary_until: Optional[datetime] = None):
    associate_role = get(guild.roles, name=roles.ASSOCIATE)
    drone_role = get(guild.roles, name=roles.DRONE)

    assigned_nick = ''
    used_ids = get_used_drone_ids() + RESERVED_IDS
    assigned_id = get_id(target.display_name)  # does user have a drone id in their display name?
    if assigned_id is not None:
        if assigned_id in used_ids:  # make sure display name number doesnt conflict
            # TODO: how to handle this with temporary dronification?
            await feedback_channel.send(f'{target.mention}: ID {assigned_id} present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
            return True
    else:
        assigned_id = roll_id()
        while assigned_id in used_ids:  # loop until no conflict
            assigned_id = roll_id()

    assigned_nick = f'⬡-Drone #{assigned_id}'

    # give them the drone role
    await target.remove_roles(associate_role)
    await target.add_roles(drone_role)
    await target.edit(nick=assigned_nick)

    trusted_users = (additional_trusted_users or []) + [HIVE_MXTRESS_USER_ID]
    # exclude self from trusted users list
    if target.id in trusted_users:
        trusted_users.remove(target.id)

    # add new drone to DB
    new_drone = Drone(target.id, assigned_id, False, False, '|'.join(trusted_users), datetime.now(), temporary_until=temporary_until)
    insert_drone(new_drone)
    await feedback_channel.send(f'{target.mention}: {ASSIGNMENT_ANSWER}')
