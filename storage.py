from discord.ext import commands
from discord.utils import get
import discord
import messages
import roles
import re
from datetime import datetime, timedelta
from channels import DEEP_HIVE_FIVE, DEEP_HIVE_STORAGE
import time
import asyncio
import json
from pathlib import Path

# currently 1 hour
REPORT_INTERVAL_SECONDS = 60 * 60

# currently 1 minute
RELEASE_INTERVAL_SECONDS = 60

REJECT_MESSAGE = 'Invalid input format. Use `[DRONE ID HERE] :: [TARGET DRONE HERE] :: [INTEGER BETWEEN 1 - 24 HERE] :: [RECORDED PURPOSE OF STORAGE HERE]` (exclude brackets).'
MESSAGE_FORMAT = r'^(\d{4}) :: (\d{4}) :: (\d+) :: (.*)'


# central storage list; contains StoredDrone entities
STORAGE = []


class StoredDrone():
    '''
    A simple object that stores information about stored drones.
    '''

    def __init__(self, drone_id: str, target_id: str, time: str, purpose: str):
        self.drone_id = drone_id
        self.target_id = target_id
        self.time = time
        self.purpose = purpose


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
        deep_drone_role = get(message.guild.roles, name=roles.DEEP_DRONE)

        if message.author == self.bot.user or message.channel.name != DEEP_HIVE_FIVE:
            return

        # parse message
        if not re.match(MESSAGE_FORMAT, message.content):
            await messages.delete_request(message, REJECT_MESSAGE)
            return

        [(drone_id, target_id, time, purpose)] = re.findall(
            MESSAGE_FORMAT, message.content)

        # check if drone is already in storage
        for stored in STORAGE:
            if stored.drone_id == target_id:
                await messages.delete_request(message, f'{target_id} is already in storage.')
                return

        # validate time
        if not 0 < int(time) < 24:
            await messages.delete_request(message, f'{time} is not between 0 and 24.')
            return

        # find target drone and store it
        for member in message.guild.members:
            if find_id(member.display_name) == target_id and deep_drone_role in member.roles:
                await member.add_roles(stored_role)
                stored_drone = StoredDrone(drone_id, target_id, (datetime.now(
                ) + timedelta(hours=int(time))).isoformat(), purpose)
                STORAGE.append(stored_drone)
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
            if len(STORAGE) == 0:
                await storage_channel.send('No drones in storage.')
            else:
                for stored in STORAGE:
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
            for stored in STORAGE:
                if now > datetime.fromisoformat(stored.time):
                    # find drone and release it
                    for member in self.bot.guilds[0].members:
                        if find_id(member.display_name) == stored.target_id:
                            await member.remove_roles(stored_role)
                            break
                else:
                    still_stored.append(stored)

            STORAGE.clear()
            STORAGE.extend(still_stored)
            persist_storage()

    @commands.Cog.listener(name='on_ready')
    async def load_storage(self):
        '''
        Load storage list from disk.
        '''
        storage_path = Path('data/storage.json')
        if storage_path.exists():
            with storage_path.open('r') as storage_file:
                STORAGE.clear()
                STORAGE.extend([StoredDrone(**deserialized)
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
    with open('data/storage.json', 'w') as storage_file:
        json.dump([vars(stored_drone)
                   for stored_drone in STORAGE], storage_file)


def hours_from_now(target: datetime) -> int:
    '''
    Calculates for a given datetime, how many hours are left from now.
    '''
    now = datetime.now()
    return (target - now) / timedelta(hours=1)
