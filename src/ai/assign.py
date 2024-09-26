import random
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import discord
from discord.utils import get

import src.messages as messages
import src.roles as roles
from src.channels import ASSIGNMENT_CHANNEL
from src.db.drone_dao import get_used_drone_ids
from src.db.data_objects import Drone
from src.bot_utils import get_id
from src.log import log
from src.db.data_objects import BatteryType

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

    # if the message is correct for being added, yay! if not, delete the message and let them know its bad
    if message.content == ASSIGNMENT_MESSAGE:
        # member has not been on the server for the required period
        if message.author.joined_at > datetime.now(timezone.utc) - timedelta(hours=24):
            log.info('Denying drone assignment. User has not existed for 24 hours.')
            await message.channel.send("Invalid request, associate must have existed on the server for at least 24 hours before dronification.")
            return False

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
    is_hive_mxtress = roles.has_role(target, roles.HIVE_MXTRESS)
    associate_name = target.display_name

    assigned_nick = ''
    used_ids = await get_used_drone_ids() + RESERVED_IDS
    assigned_id = get_id(target.display_name)  # does user have a drone id in their display name?
    if assigned_id is not None:
        if assigned_id in used_ids:  # make sure display name number doesnt conflict
            log.info('Drone creation failed: ID {assigned_id} is already assigned.')
            await feedback_channel.send(f'{target.mention}: ID {assigned_id} present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
            return True
    elif is_hive_mxtress:
        assigned_id = '0006'
    else:
        assigned_id = roll_id()
        while assigned_id in used_ids:  # loop until no conflict
            assigned_id = roll_id()

    assigned_nick = f'⬡-Drone #{assigned_id}'

    # give them the drone role
    await target.remove_roles(associate_role)
    await target.add_roles(drone_role)

    if not is_hive_mxtress:
        await target.edit(nick=assigned_nick)

    trusted_users = additional_trusted_users or []
    # exclude self from trusted users list
    if target.id in trusted_users:
        trusted_users.remove(target.id)

    # Load the default battery type.
    battery_type = await BatteryType.load(2)

    # add new drone to DB
    new_drone = Drone(
        discord_id=target.id,
        drone_id=assigned_id,
        trusted_users=trusted_users,
        last_activity=datetime.now(),
        temporary_until=temporary_until,
        can_self_configure=True,
        associate_name=associate_name,
        battery_type_id=battery_type.id,
        battery_minutes=battery_type.capacity
    )

    await new_drone.insert()
    await feedback_channel.send(f'{target.mention}: {ASSIGNMENT_ANSWER}')

    log.info(f'Created drone {assigned_id}')
