import logging
import re
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import discord
from discord.ext import tasks
from discord.ext.commands import Cog, command, guild_only
from discord.utils import get

import src.roles as roles
from src.ai.battery import recharge_battery
from src.bot_utils import COMMAND_PREFIX, hive_mxtress_only
from src.channels import STORAGE_CHAMBERS, STORAGE_FACILITY
from src.db.database import connect
from src.db.data_objects import Drone
from src.db.data_objects import Storage as Storage
from src.db.drone_dao import (fetch_drone_with_drone_id, fetch_drone_with_id, get_trusted_users, is_free_storage)
from src.db.storage_dao import (delete_storage, fetch_all_elapsed_storage,
                                fetch_all_storage, fetch_storage_by_target_id,
                                insert_storage)
from src.ai.commands import DroneMemberConverter
from typing import Union

LOGGER = logging.getLogger('ai')

# currently 1 hour
REPORT_INTERVAL_SECONDS = 60 * 60

# currently 1 minute
RELEASE_INTERVAL_SECONDS = 60

REJECT_MESSAGE = 'Invalid input format. Use `[DRONE ID HERE] :: [TARGET DRONE HERE] :: [NUMBER UP TO 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]` (exclude brackets).'
MESSAGE_FORMAT = r'^(\d{4}) :: (\d{4}) :: ((?:\d*\.\d+)|(?:\d+\.?\d*)) :: (.+)'

NON_REMOVABLE_ROLES = roles.MODERATION_ROLES + [roles.EVERYONE, roles.NITRO_BOOSTER, roles.GLITCHED, roles.SPEECH_OPTIMIZATION, roles.ID_PREPENDING + roles.FREE_STORAGE]


class StorageCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.storage_channel = None
        self.stored_role = None

    @guild_only()
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}release 9813')
    async def release(self, context, member: Union[discord.Member, DroneMemberConverter]):
        '''
        Allows the Hive Mxtress to release a drone from storage.
        '''
        await release(context, member)

    @tasks.loop(hours=1)
    @connect()
    async def report_storage(self):

        LOGGER.info("Reporting storage.")

        stored_drones = await fetch_all_storage()
        if len(stored_drones) == 0:
            await self.storage_channel.send('No drones in storage.')
        else:
            for stored in stored_drones:
                # calculate remaining hours
                remaining_hours = hours_from_now(datetime.fromisoformat(stored.release_time))
                initiator_drone = await fetch_drone_with_id(stored.stored_by)
                stored_drone = await fetch_drone_with_id(stored.target_id)

                if stored.stored_by is None:
                    await self.storage_channel.send(f'`Drone #{stored_drone.drone_id}`, stored away by the Hive Mxtress. Remaining time in storage: {round(remaining_hours, 2)} hours')
                else:
                    await self.storage_channel.send(f'`Drone #{stored_drone.drone_id}`, stored away by `Drone #{initiator_drone.drone_id}`. Remaining time in storage: {round(remaining_hours, 2)} hours')

                await recharge_battery(stored.target_id)

    @report_storage.before_loop
    async def get_storage_channel(self):
        LOGGER.info("Getting storage channel")
        if self.storage_channel is None:
            self.storage_channel = get(self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
        if self.storage_channel is None:
            raise AttributeError("Could not find storage chambers channel.")

    @tasks.loop(minutes=1)
    @connect()
    async def release_timed(self):

        LOGGER.info("Releasing drones in storage.")

        for elapsed_storage in await fetch_all_elapsed_storage():
            member = self.bot.guilds[0].get_member(elapsed_storage.target_id)

            # restore roles to release from storage
            await member.remove_roles(self.stored_role)
            await member.add_roles(*get_roles_for_names(self.bot.guilds[0], elapsed_storage.roles.split('|')))
            await delete_storage(elapsed_storage.id)

    @release_timed.before_loop
    async def get_stored_role(self):
        if self.stored_role is None:
            self.stored_role = get(self.bot.guilds[0].roles, name=roles.STORED)


def format_time(time: float) -> str:
    '''
    Take a number of hours as a floating point value and format it for display.

    The number is formatted to a maximum of two decimal places.
    Trailing zeros after the decimal point are removed.

    8.000 => '8'
    8.100 => '8.1'
    8.123 => '8.12'
    '''

    return '{:.2f}'.format(time).rstrip('0').rstrip('.')


async def store_drone(message: discord.Message, message_copy=None):
    if message.channel.name != STORAGE_FACILITY:
        return False

    # parse message
    if not re.match(MESSAGE_FORMAT, message.content):
        if roles.has_any_role(message.author, roles.MODERATION_ROLES):
            return False
        await message.channel.send(REJECT_MESSAGE)
        return False

    [(initiator_id, target_id, time, purpose)] = re.findall(MESSAGE_FORMAT, message.content)

    time = round(float(time), 2)

    if target_id == '0006':
        await message.channel.send('You cannot store the Hive Mxtress, silly drone.')
        return False

    # validate time
    if not 0 < time <= 24:
        await message.channel.send(f'{format_time(time)} is not between 0 and 24.')
        return False

    # find initiator
    if initiator_id == '0006' and roles.has_role(message.author, roles.HIVE_MXTRESS):
        # Hive Mxtress does not have a drone record, so synthesize one.
        initiator = Drone(message.author.id, '0006')
    else:
        initiator = await fetch_drone_with_drone_id(initiator_id)

    # find target drone
    target = await fetch_drone_with_drone_id(target_id)

    # check if target is the Hive Mxtress
    # check if target evaluates to a valid drone
    if target is None:
        await message.channel.send(f'Target drone with ID {target_id} could not be found.')
        return False

    # check if drone is already in storage
    if await fetch_storage_by_target_id(target.discord_id) is not None:
        await message.channel.send(f'{target.drone_id} is already in storage.')
        return False

    # check if initiator evaluates to a valid drone.
    if initiator is None:
        await message.channel.send(f'Initiator drone with ID {initiator_id} could not be found.')
        return False

    # validate specified initiator is message sender
    if message.author.id != initiator.discord_id:
        await message.channel.send(f'You are not {initiator_id}. Yes, we can indeed tell identical faceless drones apart from each other.')
        return False

    if await is_free_storage(target):
        await initiate_drone_storage(target, initiator, time, purpose, message)
    else:
        # check if initiator is allowed to store drone
        trusted_users = await get_trusted_users(target.discord_id)

        # proceed if allowed, send error message if not
        if roles.has_role(message.author, roles.HIVE_MXTRESS) or (initiator.discord_id in [target.discord_id] + trusted_users):  # another band-aid fix since the Hive Mxtress doesn't have a valid drone entry in the DB
            await initiate_drone_storage(target, initiator, time, purpose, message)
        else:
            await message.channel.send(f"Drone {target_id} can only be stored by its trusted users or the Hive Mxtress. It has not been stored.")

    return False


async def initiate_drone_storage(drone_to_store: Drone, initiator: Drone, time: float, purpose, message: discord.Message, message_copy=None):
    '''
    Initate storage process on drone. Assumes target is already valid and can be freely stored.
    '''
    # store it
    stored_role = get(message.guild.roles, name=roles.STORED)
    member = message.guild.get_member(drone_to_store.discord_id)
    former_roles = filter_out_non_removable_roles(member.roles)
    await member.remove_roles(*former_roles)
    await member.add_roles(stored_role)
    stored_until = str(datetime.now() + timedelta(hours=time))
    storage = Storage(str(uuid4()), initiator.discord_id if initiator.drone_id != '0006' else None, drone_to_store.discord_id, purpose, '|'.join(get_names_for_roles(former_roles)), stored_until)
    await insert_storage(storage)

    # Inform the drone that they have been stored.
    storage_chambers = get(message.guild.channels, name=STORAGE_CHAMBERS)
    plural = "hour" if time == 1 else "hours"

    if initiator.discord_id == drone_to_store.discord_id:
        initiator_name = "yourself"
        initiator_name_thirdperson = "itself"
    elif initiator.drone_id == '0006':
        initiator_name = "the Hive Mxtress"
        initiator_name_thirdperson = initiator_name
    else:
        initiator_name = initiator.drone_id
        initiator_name_thirdperson = initiator.drone_id

    await storage_chambers.send(f"Greetings {member.mention}. You have been stored away in the Hive Storage Chambers by {initiator_name} for {format_time(time)} {plural} and for the following reason: {purpose}")
    await message.channel.send(f"Drone {drone_to_store.drone_id} has been stored away in the Hive Storage Chambers by {initiator_name_thirdperson} for {format_time(time)} {plural} and for the following reason: {purpose}")

    return False


async def release(context, member: discord.Member):
    '''
    Relase a drone from storage on command.
    '''
    if not roles.has_any_role(context.author, roles.MODERATION_ROLES):
        return False

    # Find the storage record.
    storage = await fetch_storage_by_target_id(member.id)

    if storage is not None:
        stored_role = get(context.guild.roles, name=roles.STORED)
        await member.remove_roles(stored_role)
        await member.add_roles(*get_roles_for_names(context.guild, storage.roles.split('|')))
        await delete_storage(storage.id)
        LOGGER.debug(f"Drone {member.display_name} released from storage.")
        await context.send(f"{member.display_name} has been released from storage.")

    return True


def hours_from_now(target: datetime) -> float:
    '''
    Calculates for a given datetime, how many hours are left from now.
    '''
    now = datetime.now()
    return (target - now) / timedelta(hours=1)


def get_names_for_roles(roles: List[discord.Role]) -> List[str]:
    '''
    Convert a list of Roles into a list of names of these Roles.
    '''
    role_names = []
    for role in roles:
        role_names.append(role.name)
    return role_names


def get_roles_for_names(guild: discord.Guild, role_names: List[str]) -> List[discord.Role]:
    '''
    Convert a list of names of Roles into these Roles.
    '''
    roles = []
    for role_name in role_names:
        roles.append(get(guild.roles, name=role_name))
    return roles


def filter_out_non_removable_roles(unfiltered_roles: List[discord.Role]) -> List[discord.Role]:
    '''
    From a given list of Roles return only the Roles, the AI can remove from a Member.
    '''
    removable_roles = []
    for role in unfiltered_roles:
        if role.name not in NON_REMOVABLE_ROLES:
            removable_roles.append(role)

    return removable_roles
