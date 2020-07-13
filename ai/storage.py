import asyncio
import logging
import re
import time
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import discord
from discord.ext import commands
from discord.utils import get

import messages
import roles
from channels import STORAGE_CHAMBERS, STORAGE_FACILITY

from db.dos import Storage as StorageDO
from db.storage import insert_storage, fetch_all_storage, delete_storage, fetch_all_elapsed_storage, fetch_storage_by_target_id
from db.drone import fetch_drone_with_drone_id
from bot_utils import get_id

LOGGER = logging.getLogger('ai')

# currently 1 hour
REPORT_INTERVAL_SECONDS = 60 * 60

# currently 1 minute
RELEASE_INTERVAL_SECONDS = 60

REJECT_MESSAGE = 'Invalid input format. Use `[DRONE ID HERE] :: [TARGET DRONE HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]` (exclude brackets).'
MESSAGE_FORMAT = r'^(\d{4}) :: (\d{4}) :: (\d+) :: (.*)'

class Storage():
    '''
    This Cog manages the deep hive storage, where drones can be stored for recharging or after misbehaving.
    '''

    def __init__(self, bot):
        self.bot = bot
        self.reporter_started = False
        self.release_started = False
        self.channels_whitelist = [STORAGE_FACILITY]
        self.channels_blacklist = []
        self.roles_whitelist = [roles.HIVE_MXTRESS, roles.DRONE]
        self.roles_blacklist = []
        self.on_message = [self.release, self.store]
        self.on_ready = [self.report_storage, self.release_timed]
        self.help_content = {
            'name': 'storage', 'value': 'store your favourite drone with `[DRONE ID HERE] :: [TARGET DRONE (can be its own ID) HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]`'}

    async def store(self, message: discord.Message):
        '''
        Process posted messages.
        '''
        stored_role = get(message.guild.roles, name=roles.STORED)
        drone_role = get(message.guild.roles, name=roles.DRONE)

        # ignore help commands
        if message.content.lower() == 'help':
            return False

        # parse message
        if not re.match(MESSAGE_FORMAT, message.content):
            await message.channel.send(REJECT_MESSAGE)
            return True

        LOGGER.debug('Message is valid for storage.')
        [(drone_id, target_id, time, purpose)] = re.findall(
            MESSAGE_FORMAT, message.content)

        # check if drone is already in storage
        if fetch_storage_by_target_id(target_id) is not None:
            await message.channel.send(f'{target_id} is already in storage.')
            return True

        # validate time
        if not 0 < int(time) <= 24:
            await message.channel.send(f'{time} is not between 0 and 24.')
            return True

        # find target drone and store it
        for member in message.guild.members:
            if get_id(member.display_name) == target_id and drone_role in member.roles:
                former_roles = filter_out_non_removable_roles(member.roles)
                await member.remove_roles(*former_roles)
                await member.add_roles(stored_role)
                stored_until = str(datetime.now() + timedelta(hours=int(time)))
                stored_drone = StorageDO(str(uuid4()), drone_id, target_id, purpose, '|'.join(
                    get_names_for_roles(former_roles)), stored_until)
                insert_storage(stored_drone)

                # Inform the drone that they have been stored.
                storage_chambers = get(
                    self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
                plural = "hour" if int(time) == 1 else "hours"
                if drone_id == target_id:
                    drone_id = "yourself"
                await storage_chambers.send(f"Greetings {member.mention}. You have been stored away in the Hive Storage Chambers by {drone_id} for {time} {plural} and for the following reason: {purpose}")
                return False

        # if no drone was stored answer with error
        await message.channel.send(f'Drone with ID {target_id} could not be found.')
        return True

    async def report_storage(self):
        '''
        Report on currently stored drones.
        '''
        # only continue if there is no other reporter
        if self.reporter_started:
            return

        self.reporter_started = True
        storage_channel = get(
            self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
        while True:
            # use async sleep to avoid the bot locking up
            await asyncio.sleep(REPORT_INTERVAL_SECONDS)

            stored_drones = fetch_all_storage()
            if len(stored_drones) == 0:
                await storage_channel.send('No drones in storage.')
            else:
                for stored in stored_drones:
                    # calculate remaining hours
                    remaining_hours = hours_from_now(
                        datetime.fromisoformat(stored.release_time))
                    await storage_channel.send(f'`Drone #{stored.target_id}`, stored away by `Drone #{stored.stored_by}`. Remaining time in storage: {round(remaining_hours, 2)} hours')

    async def release_timed(self):
        '''
        Relase stored drones when the timer is up.
        '''
        if self.release_started:
            return

        self.release_started = True
        stored_role = get(self.bot.guilds[0].roles, name=roles.STORED)
        while True:
            # use async sleep to avoid the bot locking up
            await asyncio.sleep(RELEASE_INTERVAL_SECONDS)

            for elapsed_storage in fetch_all_elapsed_storage():
                drone = fetch_drone_with_drone_id(elapsed_storage.target_id)
                member = self.bot.guilds[0].get_member(drone.id)

                # restore roles to release from storage
                await member.remove_roles(stored_role)
                await member.add_roles(*get_roles_for_names(self.bot.guilds[0], elapsed_storage.roles.split('|')))
                delete_storage(elapsed_storage.id)

    async def release(self, message: discord.Message):
        '''
        Relase a drone from storage on command.
        '''
        if not message.content.lower().startswith('release'):
            return False

        LOGGER.debug('Message is valid for release.')
        if not roles.has_role(message.author, roles.HIVE_MXTRESS):
            # TODO: maybe answer with a message
            return False

        stored_role = get(message.guild.roles, name=roles.STORED)
        # find stored drone
        member = message.mentions[0]
        to_release_id = get_id(member.display_name)
        storage_to_release = fetch_storage_by_target_id(to_release_id)
        if storage_to_release is not None:
            # TODO: does this really return None or throw an error?
            drone = fetch_drone_with_drone_id(storage_to_release.target_id)
            member = self.bot.guilds[0].get_member(drone.id)
            await member.remove_roles(stored_role)
            await member.add_roles(*get_roles_for_names(message.guild, storage_to_release.roles.split('|')))
            delete_storage(storage_to_release.id)
            LOGGER.debug(
                f"Drone with ID {to_release_id} released from storage.")

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
        if role.name not in roles.MODERATION_ROLES + [roles.EVERYONE, roles.NITRO_BOOSTER, roles.PATREON_SUPPORTER]:
            removable_roles.append(role)

    return removable_roles

