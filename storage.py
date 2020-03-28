import asyncio
import json
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
from channels import DEEP_HIVE_FIVE, DEEP_HIVE_STORAGE

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

    def __init__(self, drone_id: str, target_id: str, time: str, purpose: str, roles: List[str]):
        self.drone_id = drone_id
        self.target_id = target_id
        self.time = time
        self.purpose = purpose
        self.roles = roles


class Storage(commands.Cog):
    '''
    This Cog manages the deep hive storage, where drones can be stored for recharging or after misbehaving.
    '''

    def __init__(self, bot):
        self.bot = bot
        self.reporter_started = False
        self.release_started = False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        '''
        Process posted messages.
        '''
        stored_role = get(message.guild.roles, name=roles.STORED)
        drone_role = get(message.guild.roles, name=roles.DRONE)

        if message.author == self.bot.user or message.channel.name != DEEP_HIVE_FIVE:
            return

        # parse message
        if not re.match(MESSAGE_FORMAT, message.content):
            await messages.delete_request(message, REJECT_MESSAGE)
            return

        [(drone_id, target_id, time, purpose)] = re.findall(
            MESSAGE_FORMAT, message.content)

        # check if drone is already in storage
        for stored in STORED_DRONES:
            if stored.drone_id == target_id:
                await messages.delete_request(message, f'{target_id} is already in storage.')
                return

        # validate time
        if not 0 < int(time) < 24:
            await messages.delete_request(message, f'{time} is not between 0 and 24.')
            return

        # find target drone and store it
        for member in message.guild.members:
            if find_id(member.display_name) == target_id and drone_role in member.roles:
                former_roles = filter_out_non_removable_roles(member.roles)
                await member.remove_roles(*former_roles)
                await member.add_roles(stored_role)
                stored_until = (datetime.now() +
                                timedelta(hours=int(time))).isoformat()
                stored_drone = StoredDrone(
                    drone_id, target_id, stored_until, purpose, get_names_for_roles(former_roles))
                STORED_DRONES.append(stored_drone)
                persist_storage()
                return

        # if no drone was stored answer with error
        await messages.delete_request(message, f'Drone with ID {target_id} could not be found.')

    @commands.Cog.listener(name='on_ready')
    async def report_storage(self):
        '''
        Report on currently stored drones.
        '''
        # only continue if there is no other reporter
        if self.reporter_started:
            return

        self.reporter_started = True
        storage_channel = get(
            self.bot.guilds[0].channels, name=DEEP_HIVE_STORAGE)
        while True:
            # use async sleep to avoid the bot locking up
            await asyncio.sleep(REPORT_INTERVAL_SECONDS)

            if len(STORED_DRONES) == 0:
                await storage_channel.send('No drones in storage.')
            else:
                for stored in STORED_DRONES:
                    # calculate remaining hours
                    remaining_hours = hours_from_now(
                        datetime.fromisoformat(stored.time))
                    await storage_channel.send(f'`Drone #{stored.target_id}`, stored away by `Drone #{stored.drone_id}`, stored for {round(remaining_hours, 2)} hours')

    @commands.Cog.listener(name='on_ready')
    async def release(self):
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
                if now > datetime.fromisoformat(stored.time):
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

    @commands.Cog.listener(name='on_ready')
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
    with open(STORAGE_FILE_PATH, 'w') as storage_file:
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
        if role.name not in roles.MODERATION_ROLES + [roles.EVERYONE]:
            removable_roles.append(role)

    return removable_roles
