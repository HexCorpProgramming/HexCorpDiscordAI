import re
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import discord
from discord.ext import tasks
from discord.ext.commands import Cog, command, guild_only, UserInputError
from discord.utils import get

import src.roles as roles
from src.ai.battery import recharge_battery
from src.bot_utils import COMMAND_PREFIX, hive_mxtress_only
from src.channels import STORAGE_CHAMBERS, STORAGE_FACILITY
from src.db.database import connect
from src.db.data_objects import Drone, Storage
from src.log import log
from src.drone_member import DroneMember

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
    async def release(self, context, member: DroneMember):
        '''
        Allows the Hive Mxtress to release a drone from storage.
        '''
        await release(context, member)

    @tasks.loop(hours=1)
    @connect()
    async def report_storage(self):

        log.info("Reporting storage.")

        storages = await Storage.all()

        if len(storages) == 0:
            await self.storage_channel.send('No drones in storage.')
        else:
            for storage in storages:
                # calculate remaining hours
                remaining_hours = hours_from_now(datetime.fromisoformat(storage.release_time))
                stored_drone = await Drone.load(discord_id=storage.target_id)

                if storage.stored_by is None:
                    await self.storage_channel.send(f'`Drone #{stored_drone.drone_id}`, stored away by the Hive Mxtress. Remaining time in storage: {round(remaining_hours, 2)} hours')
                else:
                    initiator_drone = await Drone.load(discord_id=storage.stored_by)
                    await self.storage_channel.send(f'`Drone #{stored_drone.drone_id}`, stored away by `Drone #{initiator_drone.drone_id}`. Remaining time in storage: {round(remaining_hours, 2)} hours')

                await recharge_battery(stored_drone)

    @report_storage.before_loop
    async def get_storage_channel(self):
        if self.storage_channel is None:
            self.storage_channel = get(self.bot.guilds[0].channels, name=STORAGE_CHAMBERS)
        if self.storage_channel is None:
            raise AttributeError("Could not find storage chambers channel.")

    @tasks.loop(minutes=1)
    @connect()
    async def release_timed(self):
        guild = self.bot.guilds[0]

        for member in await Storage.all_elapsed(guild):
            # restore roles to release from storage
            await member.remove_roles(self.stored_role)
            await member.add_roles(*get_roles_for_names(guild, member.roles.split('|')))
            await member.drone.storage.delete()

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

        raise UserInputError(REJECT_MESSAGE)

    [(initiator_id, target_id, time, purpose)] = re.findall(MESSAGE_FORMAT, message.content)

    time = round(float(time), 2)

    if target_id == '0006':
        raise UserInputError('You cannot store the Hive Mxtress, silly drone.')

    # validate time
    if not 0 < time <= 24:
        raise UserInputError(f'{format_time(time)} is not between 0 and 24.')

    # find initiator
    if initiator_id == '0006' and roles.has_role(message.author, roles.HIVE_MXTRESS):
        initiator = await DroneMember.load(message.guild, discord_id=message.author.id)
    else:
        initiator = await DroneMember.find(message.guild, drone_id=initiator_id)

    # find target drone
    target = await DroneMember.find(drone_id=target_id)

    # check if target evaluates to a valid drone
    if target is None or target.drone is None:
        raise UserInputError(f'Target drone with ID {target_id} could not be found.')

    # check if drone is already in storage
    if target.drone.storage is not None:
        raise UserInputError(f'{target.drone.drone_id} is already in storage.')

    # check if initiator evaluates to a valid drone.
    if initiator is None:
        raise UserInputError(f'Initiator drone with ID {initiator_id} could not be found.')

    # validate specified initiator is message sender
    if message.author.id != initiator.id:
        raise UserInputError(f'You are not {initiator_id}. Yes, we can indeed tell identical faceless drones apart from each other.')

    if not target.drone.allows_storage_by(initiator):
        raise UserInputError(f"Drone {target_id} can only be stored by its trusted users or the Hive Mxtress. It has not been stored.")

    await initiate_drone_storage(target, initiator, time, purpose, message)

    return False


async def initiate_drone_storage(drone_to_store: DroneMember, initiator: DroneMember, time: float, purpose, message: discord.Message, message_copy=None):
    '''
    Initate storage process on drone. Assumes target is already valid and can be freely stored.
    '''
    # store it
    stored_role = get(message.guild.roles, name=roles.STORED)
    former_roles = filter_out_non_removable_roles(drone_to_store.roles)
    await drone_to_store.remove_roles(*former_roles)
    await drone_to_store.add_roles(stored_role)
    stored_until = str(datetime.now() + timedelta(hours=time))
    storage = Storage(str(uuid4()), initiator.id, drone_to_store.id, purpose, '|'.join(get_names_for_roles(former_roles)), stored_until)
    await storage.insert()

    # Inform the drone that they have been stored.
    storage_chambers = get(message.guild.channels, name=STORAGE_CHAMBERS)
    plural = "hour" if time == 1 else "hours"

    if initiator.id == drone_to_store.id:
        initiator_name = "yourself"
        initiator_name_thirdperson = "itself"
    elif not initiator.drone:
        initiator_name = "the Hive Mxtress"
        initiator_name_thirdperson = initiator_name
    else:
        initiator_name = initiator.drone.drone_id
        initiator_name_thirdperson = initiator.drone.drone_id

    await storage_chambers.send(f"Greetings {drone_to_store.mention}. You have been stored away in the Hive Storage Chambers by {initiator_name} for {format_time(time)} {plural} and for the following reason: {purpose}")
    await message.channel.send(f"Drone {drone_to_store.drone.drone_id} has been stored away in the Hive Storage Chambers by {initiator_name_thirdperson} for {format_time(time)} {plural} and for the following reason: {purpose}")

    return False


async def release(context, member: DroneMember):
    '''
    Relase a drone from storage on command.
    '''

    if not roles.has_any_role(context.author, roles.MODERATION_ROLES):
        return False

    storage = member.storage

    if storage is not None:
        stored_role = get(context.guild.roles, name=roles.STORED)
        await member.remove_roles(stored_role)
        await member.add_roles(*get_roles_for_names(context.guild, storage.roles.split('|')))
        await storage.delete()
        log.debug(f"Drone {member.display_name} released from storage.")
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
