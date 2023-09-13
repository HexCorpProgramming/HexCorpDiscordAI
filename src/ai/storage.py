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
from src.bot_utils import COMMAND_PREFIX
from src.channels import STORAGE_CHAMBERS, STORAGE_FACILITY
from src.db.data_objects import Drone as DroneDO
from src.db.data_objects import Storage as StorageDO
from src.db.drone_dao import fetch_drone_with_drone_id, is_free_storage, get_trusted_users
from src.db.storage_dao import (delete_storage, fetch_all_elapsed_storage,
                                fetch_all_storage, fetch_storage_by_target_id,
                                insert_storage)
from src.id_converter import convert_id_to_member
from src.resources import BRIEF_HIVE_MXTRESS, HIVE_MXTRESS_USER_ID

LOGGER = logging.getLogger('ai')

# currently 1 hour
REPORT_INTERVAL_SECONDS = 60 * 60

# currently 1 minute
RELEASE_INTERVAL_SECONDS = 60

REJECT_MESSAGE = 'Invalid input format. Use `[DRONE ID HERE] :: [TARGET DRONE HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]` (exclude brackets).'
MESSAGE_FORMAT = r'^(\d{4}) :: (\d{4}) :: (\d+) :: (.*)'

NON_REMOVABLE_ROLES = roles.MODERATION_ROLES + [roles.EVERYONE, roles.NITRO_BOOSTER, roles.GLITCHED, roles.SPEECH_OPTIMIZATION, roles.ID_PREPENDING + roles.FREE_STORAGE]


class StorageCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.storage_channel = None
        self.stored_role = None

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}release 9813', brief=[BRIEF_HIVE_MXTRESS])
    async def release(self, context, drone):
        '''
        Allows the Hive Mxtress to release a drone from storage.
        '''
        await release(context, drone)

    @tasks.loop(hours=1)
    async def report_storage(self):

        LOGGER.info("Reporting storage.")

        stored_drones = fetch_all_storage()
        if len(stored_drones) == 0:
            await self.storage_channel.send('No drones in storage.')
        else:
            for stored in stored_drones:
                # calculate remaining hours
                remaining_hours = hours_from_now(
                    datetime.fromisoformat(stored.release_time))
                if stored.stored_by == '0006':
                    await self.storage_channel.send(f'`Drone #{stored.target_id}`, stored away by the Hive Mxtress. Remaining time in storage: {round(remaining_hours, 2)} hours')
                else:
                    await self.storage_channel.send(f'`Drone #{stored.target_id}`, stored away by `Drone #{stored.stored_by}`. Remaining time in storage: {round(remaining_hours, 2)} hours')
                recharge_battery(stored)

    @report_storage.before_loop
    async def get_storage_channel(self):
        LOGGER.info("Getting storage channel")
        if self.storage_channel is None:
            self.storage_channel = get(self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
        if self.storage_channel is None:
            raise AttributeError("Could not find storage chambers channel.")

    @tasks.loop(minutes=1)
    async def release_timed(self):

        LOGGER.info("Releasing drones in storage.")

        for elapsed_storage in fetch_all_elapsed_storage():
            drone = fetch_drone_with_drone_id(elapsed_storage.target_id)
            member = self.bot.guilds[0].get_member(drone.id)

            # restore roles to release from storage
            await member.remove_roles(self.stored_role)
            await member.add_roles(*get_roles_for_names(self.bot.guilds[0], elapsed_storage.roles.split('|')))
            delete_storage(elapsed_storage.id)

    @release_timed.before_loop
    async def get_stored_role(self):
        if self.stored_role is None:
            self.stored_role = get(self.bot.guilds[0].roles, name=roles.STORED)


async def store_drone(message: discord.Message, message_copy=None):
    if message.channel.name != STORAGE_FACILITY:
        return False

    # parse message
    if not re.match(MESSAGE_FORMAT, message.content):
        if roles.has_any_role(message.author, roles.MODERATION_ROLES):
            return False
        await message.channel.send(REJECT_MESSAGE)
        return False

    LOGGER.debug('Message is valid for storage.')
    [(drone_id, target_id, time, purpose)] = re.findall(
        MESSAGE_FORMAT, message.content)

    # check if drone is already in storage
    if fetch_storage_by_target_id(target_id) is not None:
        await message.channel.send(f'{target_id} is already in storage.')
        return False

    # validate time
    if not 0 < int(time) <= 24:
        await message.channel.send(f'{time} is not between 0 and 24.')
        return False

    # check if target is the Hive Mxtress
    if target_id == '0006':
        await message.channel.send('You cannot store the Hive Mxtress, silly drone.')
        return False

    # find initiator
    initiator = fetch_drone_with_drone_id(drone_id)

    # validate specified initiator is message sender
    if (not (drone_id == '0006' and roles.has_role(message.author, roles.HIVE_MXTRESS))) and (message.author.id != initiator.id):  # temp fix while we decide what to do with the db missing a drone entry for the Hive Mxtress
        await message.channel.send(f'You are not {drone_id}. Yes, we can indeed tell identical faceless drones apart from each other.')
        return False

    # find target drone
    drone_to_store = fetch_drone_with_drone_id(target_id)

    # if no drone was stored answer with error
    if drone_to_store is None:
        await message.channel.send(f'Drone with ID {target_id} could not be found.')
        return False

    if is_free_storage(drone_to_store):
        await initiate_drone_storage(drone_to_store, drone_id, target_id, time, purpose, message)
    else:
        # check if initiator is allowed to store drone
        trusted_users = get_trusted_users(drone_to_store.id)

        # proceed if allowed, send error message if not
        if initiator.id in [HIVE_MXTRESS_USER_ID, drone_to_store.id] + trusted_users:
            await initiate_drone_storage(drone_to_store, drone_id, target_id, time, purpose, message)
        else:
            await message.channel.send(f"Drone {target_id} can only be stored by its trusted users or the Hive Mxtress. It has not been stored.")
    return False


async def initiate_drone_storage(drone_to_store: DroneDO, drone_id, target_id, time, purpose, message: discord.Message, message_copy=None):
    '''
    Initate storage process on drone. Assumes target is already valid and can be freely stored.
    '''
    # store it
    stored_role = get(message.guild.roles, name=roles.STORED)
    member = message.guild.get_member(drone_to_store.id)
    former_roles = filter_out_non_removable_roles(member.roles)
    await member.remove_roles(*former_roles)
    await member.add_roles(stored_role)
    stored_until = str(datetime.now() + timedelta(hours=int(time)))
    stored_drone = StorageDO(str(uuid4()), drone_id, target_id, purpose, '|'.join(get_names_for_roles(former_roles)), stored_until)
    insert_storage(stored_drone)

    # Inform the drone that they have been stored.
    storage_chambers = get(message.guild.channels, name=STORAGE_CHAMBERS)
    plural = "hour" if int(time) == 1 else "hours"
    if drone_id == target_id:
        drone_id = "yourself"
        drone_id_thirdperson = "itself"
    elif drone_id == '0006':
        drone_id = drone_id_thirdperson = "the Hive Mxtress"
    else:
        drone_id_thirdperson = drone_id
    await storage_chambers.send(f"Greetings {member.mention}. You have been stored away in the Hive Storage Chambers by {drone_id} for {time} {plural} and for the following reason: {purpose}")
    await message.channel.send(f"Drone {target_id} has been stored away in the Hive Storage Chambers by {drone_id_thirdperson} for {time} {plural} and for the following reason: {purpose}")

    return False


async def release(context, stored_drone: str):
    '''
    Relase a drone from storage on command.
    '''
    if not roles.has_any_role(context.author, roles.MODERATION_ROLES):
        return False

    release_id = stored_drone
    stored_drone = convert_id_to_member(context.guild, stored_drone)

    if stored_drone is None:
        return True

    stored_role = get(context.guild.roles, name=roles.STORED)
    # find stored drone
    stored_drone_data = fetch_storage_by_target_id(release_id)
    if stored_drone_data is not None:
        await stored_drone.remove_roles(stored_role)
        await stored_drone.add_roles(*get_roles_for_names(context.guild, stored_drone_data.roles.split('|')))
        delete_storage(stored_drone_data.id)
        LOGGER.debug(
            f"Drone with ID {release_id} released from storage.")
        await context.send(f"{stored_drone.display_name} has been released from storage.")
    return True


def hours_from_now(target: datetime) -> int:
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
