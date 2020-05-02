import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import discord
from discord.ext import commands
from discord.utils import get

import messages
import roles
from channels import STORAGE_CHAMBERS, STORAGE_FACILITY

LOGGER = logging.getLogger('ai')

# currently 1 hour
REPORT_INTERVAL_SECONDS = 60 * 60

# currently 1 minute
RELEASE_INTERVAL_SECONDS = 60

REJECT_MESSAGE = 'Invalid input format. Use `[DRONE ID HERE] :: [TARGET DRONE HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]` (exclude brackets).'
MESSAGE_FORMAT = r'^(\d{4}) :: (\d{4}) :: (\d+) :: (.*)'

# path to the file where information about stored drones is kept
STORAGE_FILE_PATH = 'data/storage.json'

# central storage list; contains StoredDrone entities
STORED_DRONES = []


class StoredDrone():
    '''
    A simple object that stores information about stored drones.
    '''

    def __init__(self, drone_id: str, target_id: str, release_time: str, purpose: str, roles: List[str]):
        self.drone_id = drone_id
        self.target_id = target_id
        self.release_time = release_time
        self.purpose = purpose
        self.roles = roles


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
        self.on_ready = [self.load_storage, self.report_storage, self.release_timed]
        self.help_content = {'name': 'storage', 'value': 'store your favourite drone with `[DRONE ID HERE] :: [TARGET DRONE (can be its own ID) HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]`'}

    async def store(self, message: discord.Message):
        '''
        Process posted messages.
        '''
        stored_role = get(message.guild.roles, name=roles.STORED)
        drone_role = get(message.guild.roles, name=roles.DRONE)

        # ignore help commands
        if message.content.lower() == ('help'):
            return False

        # parse message
        if not re.match(MESSAGE_FORMAT, message.content):
            await message.channel.send(REJECT_MESSAGE)
            return True

        [(drone_id, target_id, time, purpose)] = re.findall(
            MESSAGE_FORMAT, message.content)

        # check if drone is already in storage
        for stored in STORED_DRONES:
            if stored.target_id == target_id:
                await message.channel.send(f'{target_id} is already in storage.')
                return True

        # validate time
        if not 0 < int(time) <= 24:
            await message.channel.send(f'{time} is not between 0 and 24.')
            return True

        # find target drone and store it
        for member in message.guild.members:
            if find_id(member.display_name) == target_id and drone_role in member.roles:
                former_roles = filter_out_non_removable_roles(member.roles)
                await member.remove_roles(*former_roles)
                await member.add_roles(stored_role)
                stored_until = (datetime.now() +
                                timedelta(hours=int(time))).timestamp()
                stored_drone = StoredDrone(
                    drone_id, target_id, stored_until, purpose, get_names_for_roles(former_roles))
                STORED_DRONES.append(stored_drone)
                persist_storage()

                #Inform the drone that they have been stored.
                storage_chambers = get(self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
                plural = "hour" if int(time) == 1 else "hours"
                if drone_id == target_id:
                    drone_id == "yourself"
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

            if len(STORED_DRONES) == 0:
                await storage_channel.send('No drones in storage.')
            else:
                for stored in STORED_DRONES:
                    # calculate remaining hours
                    remaining_hours = hours_from_now(
                        datetime.fromtimestamp(stored.release_time))
                    await storage_channel.send(f'`Drone #{stored.target_id}`, stored away by `Drone #{stored.drone_id}`. Remaining time in storage: {round(remaining_hours, 2)} hours')

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

            still_stored = []
            now = datetime.now()
            for stored in STORED_DRONES:
                if now > datetime.fromtimestamp(stored.release_time):
                    # find drone member
                    for member in self.bot.guilds[0].members:
                        if find_id(member.display_name) == stored.target_id:
                            # restore roles to release from storage
                            await member.remove_roles(stored_role)
                            await member.add_roles(*get_roles_for_names(self.bot.guilds[0], stored.roles))
                            break
                else:
                    still_stored.append(stored)

            STORED_DRONES.clear()
            STORED_DRONES.extend(still_stored)
            persist_storage()

    async def load_storage(self):
        '''
        Load storage list from disk.
        '''
        storage_path = Path(STORAGE_FILE_PATH)
        if not storage_path.exists():
            return

        with storage_path.open('r') as storage_file:
            STORED_DRONES.clear()
            STORED_DRONES.extend([StoredDrone(**deserialized)
                                  for deserialized in json.load(storage_file)])

    async def release(self, message: discord.Message):
        '''
        Relase a drone from storage on command.
        '''
        if not message.content.lower().startswith('release'):
            return False

        if not roles.has_role(message.author, roles.HIVE_MXTRESS):
            # TODO: maybe answer with a message
            return False

        stored_role = get(message.guild.roles, name=roles.STORED)
        # find stored drone
        member = message.mentions[0]
        to_release_id = find_id(member.display_name)
        for drone in STORED_DRONES:
            if drone.target_id == to_release_id:
                await member.remove_roles(stored_role)
                await member.add_roles(*get_roles_for_names(message.guild, drone.roles))
                STORED_DRONES.remove(drone)
                persist_storage()
                LOGGER.debug(f"Drone with ID {to_release_id} released from storage.")
                return True
        return True


def find_id(name: str) -> str:
    '''
    Find the four digit ID in a nickname.
    '''
    matches = re.findall(r'\d{4}', name)
    if len(matches) == 0:
        return ''
    else:
        return matches[0]


def persist_storage():
    '''
    Write the list of stored drones to hard drive.
    '''
    storage_path = Path(STORAGE_FILE_PATH)
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    with storage_path.open('w') as storage_file:
        json.dump([vars(stored_drone)
                   for stored_drone in STORED_DRONES], storage_file)


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
