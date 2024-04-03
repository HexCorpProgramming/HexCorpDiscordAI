import logging
import re
from typing import Union
from copy import deepcopy
from typing import Dict, List
from src.ai.data_objects import MessageCopy
from src.db.database import connect

from discord import Emoji, Guild, Member, Message
from discord.ext import commands, tasks
from discord.ext.commands import command
from discord.utils import get

import src.emoji as emoji
import src.webhook as webhook
from src.ai.identity_enforcement import identity_enforcable
from src.id_converter import convert_ids_to_members
from src.resources import (BRIEF_HIVE_MXTRESS, DRONE_AVATAR)
from src.roles import BATTERY_DRAINED, BATTERY_POWERED, HIVE_MXTRESS, has_role
from src.bot_utils import COMMAND_PREFIX, get_id
from src.ai.commands import DroneMemberConverter
from src.db.drone_dao import (deincrement_battery_minutes_remaining,
                              fetch_drone_with_id,
                              get_all_drone_batteries,
                              get_battery_minutes_remaining,
                              get_battery_percent_remaining,
                              get_battery_type,
                              get_battery_types,
                              is_battery_powered, is_drone,
                              set_battery_minutes_remaining,
                              set_battery_type)

LOGGER = logging.getLogger('ai')


class BatteryCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.draining_batteries: Dict[str, int] = {}  # {drone_id: minutes of drain left}
        self.low_battery_drones: List[str] = []  # [drone_id]

    @command(usage=f"{COMMAND_PREFIX}set_battery_type 3287 low", brief=[BRIEF_HIVE_MXTRESS])
    async def set_battery_type(self, context, member: Union[Member, DroneMemberConverter], type_name: str):
        '''
        Hive Mxtress only command.
        Recharges a drone to 100% battery.
        '''

        if not has_role(context.message.author, HIVE_MXTRESS):
            return

        drone = await fetch_drone_with_id(member.id)

        if drone is None:
            # TODO: Throw a ValidationError once that PR is merged.
            await context.send('Member ' + member.display_name + ' is not a drone')
            return

        battery_types = await get_battery_types()
        type = next((t for t in battery_types if t.name.lower() == type_name.lower()), None)

        if type is None:
            # TODO: Throw a ValidationError once that PR is merged.
            await context.send('Invalid battery type "' + type_name + '". Valid battery types are: ' + ', '.join([t.name for t in battery_types]))
            return

        await set_battery_type(member, type)
        await context.send('Battery type for drone ' + drone.drone_id + ' is now: ' + type.name)

    @command(usage=f"{COMMAND_PREFIX}energize 3287", brief=[BRIEF_HIVE_MXTRESS])
    async def energize(self, context, *drone_ids):
        '''
        Hive Mxtress only command.
        Recharges a drone to 100% battery.
        '''
        if not has_role(context.message.author, HIVE_MXTRESS):
            return

        LOGGER.info("Energize command envoked.")

        for member in set(context.message.mentions) | await convert_ids_to_members(context.guild, drone_ids):

            LOGGER.info(f"Energizing {member.display_name}")

            battery_type = await get_battery_type(member)

            await set_battery_minutes_remaining(member, battery_type.capacity)
            channel_webhook = await webhook.get_webhook_for_channel(context.message.channel)
            await webhook.proxy_message_by_webhook(message_content=f'{get_id(member.display_name)} :: This unit is fully recharged. Thank you Hive Mxtress.',
                                                   message_username=member.display_name,
                                                   message_avatar=DRONE_AVATAR if await identity_enforcable(member, channel=context.message.channel) else (member.avatar.url if member.avatar else None),
                                                   webhook=channel_webhook)

    @command(usage=f"{COMMAND_PREFIX}drain 3287", brief=[BRIEF_HIVE_MXTRESS])
    async def drain(self, context, *drone_ids):
        '''
        Hive Mxtress only command.
        Drains a drone's battery by 10%.
        '''
        if not has_role(context.message.author, HIVE_MXTRESS):
            return

        LOGGER.info("Drain command envoked.")

        for drone in set(context.message.mentions) | await convert_ids_to_members(context.guild, drone_ids):

            if not await is_battery_powered(drone):
                await context.send(f"{drone.nick} cannot be drained, it is currently connected to the HexCorp power grid.")
                continue

            LOGGER.info(f"Draining {drone.display_name}")

            await drain_battery(member=drone)
            percentage_remaining = await get_battery_percent_remaining(drone)
            channel_webhook = await webhook.get_webhook_for_channel(context.message.channel)
            await webhook.proxy_message_by_webhook(message_content=f'{get_id(drone.display_name)} :: Drone battery has been forcibly drained. Remaining battery now at {percentage_remaining}%',
                                                   message_username=drone.display_name,
                                                   message_avatar=DRONE_AVATAR if await identity_enforcable(drone, channel=context.message.channel) else drone.avatar.url,
                                                   webhook=channel_webhook)

    async def start_battery_drain(self, message, message_copy=None):
        '''
        If message author has battery DroneOS config enabled, begin or restart
        tracking them for 15 minutes worth of battery drain per message sent.
        '''

        if not await is_drone(message.author) or not await is_battery_powered(message.author):
            return False

        drone_id = get_id(message.author.display_name)
        self.draining_batteries[drone_id] = 15

    @tasks.loop(minutes=1)
    @connect()
    async def track_active_battery_drain(self):
        LOGGER.info("Draining battery from active drones.")

        inactive_drones = []
        # make a copy in case there is simultaneous modification
        draining_batteries = deepcopy(self.draining_batteries)

        for drone, remaining_minutes in draining_batteries.items():
            if drone is None:
                LOGGER.warn("drone is None; skipping")
                continue

            if remaining_minutes <= 0:
                LOGGER.info(f"Drone {drone} has been idle for 15 minutes. No longer draining power.")
                # Cannot alter list while iterating, so add drone to list of drones to pop after the loop.
                inactive_drones.append(drone)
            else:
                LOGGER.info(f"Draining 1 minute worth of charge from {drone}")
                draining_batteries[drone] = remaining_minutes - 1
                await deincrement_battery_minutes_remaining(drone_id=drone)

        for inactive_drone in inactive_drones:
            LOGGER.info(f"Removing {inactive_drone} from drain list.")
            draining_batteries.pop(inactive_drone)

        self.draining_batteries = draining_batteries

    @tasks.loop(minutes=1)
    @connect()
    async def track_drained_batteries(self):
        # Every drone has a battery. If battery_minutes = 0, give the Drained role.
        # If battery_minutes > 0 and it has the Drained role, remove it.
        # Since this is independent of having the Battery role, this should work even if the config is disabled.

        LOGGER.info("Checking for drones with drained battery.")

        for drone in await get_all_drone_batteries():
            # Intentionally different math to that in DAO b/c it always rounds down.
            member_drone = self.bot.guilds[0].get_member(drone.discord_id)

            if member_drone is None:
                LOGGER.warn(f"Drone {drone.drone_id} not found in server but present in database.")
                continue

            if drone.battery_minutes <= 0 and has_role(member_drone, BATTERY_POWERED):
                LOGGER.debug(f"Drone {drone.drone_id} is out of battery. Adding drained role.")
                await member_drone.add_roles(get(self.bot.guilds[0].roles, name=BATTERY_DRAINED))
            elif drone.battery_minutes > 0 and has_role(member_drone, BATTERY_DRAINED):
                LOGGER.debug(f"Drone {drone.drone_id} has been recharged. Removing drained role.")
                await member_drone.remove_roles(get(self.bot.guilds[0].roles, name=BATTERY_DRAINED))

    @tasks.loop(minutes=1)
    @connect()
    async def warn_low_battery_drones(self):
        '''
        DMs any drone below 30% battery to remind them to charge.
        The drone will be added to a list so the AI does not forget.
        Drones will be removed from the list once their battery is greater than 30% again.
        '''

        LOGGER.info("Scanning for low battery drones.")

        for drone in await get_all_drone_batteries():
            member = self.bot.guilds[0].get_member(drone.discord_id)

            if member is None:
                LOGGER.warn(f"Drone {drone.drone_id} not found in server but present in database.")
                continue

            if await get_battery_percent_remaining(member) < 30:
                if drone.drone_id not in self.low_battery_drones:
                    LOGGER.info(f"Warning drone {drone.drone_id} of low battery.")
                    await member.send("Attention. Your battery is low (30%). Please connect to main power grid in the Storage Facility immediately.")
                    self.low_battery_drones.append(drone.drone_id)
            else:
                # Attempt to remove them from the list of warned users.
                if drone.drone_id in self.low_battery_drones:
                    LOGGER.info(f"Drone {drone.drone_id} has recharged above 30%. Good drone.")
                    try:
                        self.low_battery_drones.remove(drone.drone_id)
                    except ValueError:
                        continue


async def add_battery_indicator_to_copy(message: Message, message_copy: MessageCopy):
    '''
    Prepends battery indicator emoji to a MessageCopy if the drone
    which sent the original message is battery powered.
    The indicator is placed after the ID prepend if the message includes it.
    '''
    message_copy.content = await generate_battery_message(message.author, message_copy.content)

    return False


async def generate_battery_message(member: Member, original_content: str) -> str:
    '''
    Assembles a message content with a battery emoji for a given Guild Member.
    Returns the original content if the drone is not battery powered.
    '''

    if not await is_battery_powered(member):
        return original_content

    battery_percentage = await get_battery_percent_remaining(member)
    battery_emoji = determine_battery_emoji(battery_percentage, member.guild)

    id_prepending_regex = re.compile(r'(\d{4} ::)(.+)', re.DOTALL)

    id_prepending_message = id_prepending_regex.match(original_content)

    if id_prepending_message:
        return f"{id_prepending_message.group(1)} {str(battery_emoji)} ::{id_prepending_message.group(2)}"
    else:
        return f"{str(battery_emoji)} :: {original_content}"


def determine_battery_emoji(battery_percentage: int, guild: Guild) -> Emoji | str:
    '''
    Determines which battery emoji should be used according to the charge of the drone.
    '''

    if battery_percentage <= 100 and battery_percentage >= 75:
        return get(guild.emojis, name=emoji.BATTERY_FULL)
    elif battery_percentage <= 75 and battery_percentage >= 25:
        return get(guild.emojis, name=emoji.BATTERY_MID)
    elif battery_percentage <= 24 and battery_percentage >= 10:
        return get(guild.emojis, name=emoji.BATTERY_LOW)
    elif battery_percentage <= 9:
        return get(guild.emojis, name=emoji.BATTERY_EMPTY)
    else:
        return "[BATTERY ERROR]"


async def recharge_battery(member: Member) -> None:
    '''
    Fills the battery of a drone in storage up to max.
    '''

    current_minutes_remaining = await get_battery_minutes_remaining(member)
    battery_type = await get_battery_type(member)
    await set_battery_minutes_remaining(member, min(battery_type.capacity, current_minutes_remaining + battery_type.recharge_rate))


async def drain_battery(member: Member):
    '''
    Reduces the battery charge of a drone by 10%.
    '''

    minutes_remaining = await get_battery_minutes_remaining(member)
    battery_type = await get_battery_type(member)

    await set_battery_minutes_remaining(member, minutes_remaining - battery_type.capacity / 10)
