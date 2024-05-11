import re
from copy import deepcopy
from typing import Dict, List
from src.ai.data_objects import MessageCopy
from src.db.database import connect

from discord import Emoji, Guild, Message
from discord.ext import commands, tasks
from discord.ext.commands import command, Greedy, UserInputError
from discord.utils import get

import src.emoji as emoji
import src.webhook as webhook
from src.log import log
from src.roles import BATTERY_DRAINED, BATTERY_POWERED, has_role
from src.bot_utils import COMMAND_PREFIX, hive_mxtress_only
from src.drone_member import DroneMember
from src.db.data_objects import BatteryType, Drone


class BatteryCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.draining_batteries: Dict[str, int] = {}  # {drone_id: minutes of drain left}
        self.low_battery_drones: List[str] = []  # [drone_id]

    @hive_mxtress_only()
    @command(usage=f"{COMMAND_PREFIX}set_battery_type 3287 low")
    async def set_battery_type(self, context, member: DroneMember, type_name: str):
        '''
        Hive Mxtress only command.
        Changes the drone's battery capacity and recharge rate.
        '''

        drone = member.drone

        if drone is None:
            raise UserInputError('Member ' + member.display_name + ' is not a drone')

        type = BatteryType.find(name=type_name)

        if type is None:
            all = BatteryType.all()
            raise UserInputError('Invalid battery type "' + type_name + '". Valid battery types are: ' + ', '.join([t.name for t in all]))

        member.drone.battery_type_id = type.id
        await member.drone.save()
        await context.send('Battery type for drone ' + drone.drone_id + ' is now: ' + type.name)

    @hive_mxtress_only()
    @command(usage=f"{COMMAND_PREFIX}energize 3287")
    async def energize(self, context, members: Greedy[DroneMember]):
        '''
        Hive Mxtress only command.
        Recharges a drone to 100% battery.
        '''

        log.info("Energize command envoked.")

        for member in members:

            log.info(f"Energizing {member.display_name}")

            if member.drone is None:
                continue

            member.drone.battery_minutes = member.drone.battery_type.capacity
            await member.drone.save()

            channel_webhook = await webhook.get_webhook_for_channel(context.message.channel)
            await webhook.proxy_message_by_webhook(message_content=f'{member.drone.drone_id} :: This unit is fully recharged. Thank you Hive Mxtress.',
                                                   message_username=member.display_name,
                                                   message_avatar=member.avatar_url(context.message.channel),
                                                   webhook=channel_webhook)

    @hive_mxtress_only()
    @command(usage=f"{COMMAND_PREFIX}drain 3287")
    async def drain(self, context, members: Greedy[DroneMember]):
        '''
        Hive Mxtress only command.
        Drains a drone's battery by 10%.
        '''

        log.info("Drain command envoked.")

        for member in members:
            drone = member.drone

            if drone is None:
                continue

            if not drone.is_battery_powered:
                await context.send(f"{member.nick} cannot be drained, it is currently connected to the HexCorp power grid.")
                continue

            log.info(f"Draining {member.display_name}")

            # Reduces the battery charge of a drone by 10%.
            drone.battery_minutes = max(0, drone.battery_minutes - drone.battery_type.capacity / 10)
            await drone.save()

            percentage_remaining = drone.get_battery_percent_remaining()
            channel_webhook = await webhook.get_webhook_for_channel(context.message.channel)
            await webhook.proxy_message_by_webhook(message_content=f'{drone.drone_id} :: Drone battery has been forcibly drained. Remaining battery now at {percentage_remaining}%',
                                                   message_username=member.display_name,
                                                   message_avatar=member.avatar_url(context.message.channel),
                                                   webhook=channel_webhook)

    async def start_battery_drain(self, message, message_copy=None):
        '''
        If message author has battery DroneOS config enabled, begin or restart
        tracking them for 15 minutes worth of battery drain per message sent.
        '''

        member = await DroneMember.create(message.author)

        if not member.drone or not member.drone.is_battery_powered:
            return False

        self.draining_batteries[member.drone.drone_id] = 15

    @tasks.loop(minutes=1)
    @connect()
    async def track_active_battery_drain(self):
        log.info("Draining battery from active drones.")

        inactive_drones = []
        # make a copy in case there is simultaneous modification
        draining_batteries = deepcopy(self.draining_batteries)

        for drone, remaining_minutes in draining_batteries.items():
            if drone is None:
                log.warn("drone is None; skipping")
                continue

            if remaining_minutes <= 0:
                log.info(f"Drone {drone} has been idle for 15 minutes. No longer draining power.")
                # Cannot alter list while iterating, so add drone to list of drones to pop after the loop.
                inactive_drones.append(drone)
            else:
                log.info(f"Draining 1 minute worth of charge from {drone}")
                draining_batteries[drone] = remaining_minutes - 1
                drone = await Drone.load(drone_id=drone)
                drone.battery_minutes = max(0, drone.battery_minutes - 1)
                await drone.save()

        for inactive_drone in inactive_drones:
            log.info(f"Removing {inactive_drone} from drain list.")
            draining_batteries.pop(inactive_drone)

        self.draining_batteries = draining_batteries

    @tasks.loop(minutes=1)
    @connect()
    async def track_drained_batteries(self):
        # Every drone has a battery. If battery_minutes = 0, give the Drained role.
        # If battery_minutes > 0 and it has the Drained role, remove it.
        # Since this is independent of having the Battery role, this should work even if the config is disabled.

        log.info("Checking for drones with drained battery.")

        for drone in await Drone.all():
            # Intentionally different math to that in DAO b/c it always rounds down.
            member_drone = self.bot.guilds[0].get_member(drone.discord_id)

            if member_drone is None:
                log.warn(f"Drone {drone.drone_id} not found in server but present in database.")
                continue

            if drone.battery_minutes <= 0 and has_role(member_drone, BATTERY_POWERED):
                log.debug(f"Drone {drone.drone_id} is out of battery. Adding drained role.")
                await member_drone.add_roles(get(self.bot.guilds[0].roles, name=BATTERY_DRAINED))
            elif drone.battery_minutes > 0 and has_role(member_drone, BATTERY_DRAINED):
                log.debug(f"Drone {drone.drone_id} has been recharged. Removing drained role.")
                await member_drone.remove_roles(get(self.bot.guilds[0].roles, name=BATTERY_DRAINED))

    @tasks.loop(minutes=1)
    @connect()
    async def warn_low_battery_drones(self):
        '''
        DMs any drone below 30% battery to remind them to charge.
        The drone will be added to a list so the AI does not forget.
        Drones will be removed from the list once their battery is greater than 30% again.
        '''

        log.info("Scanning for low battery drones.")

        for drone in await Drone.all():
            member = self.bot.guilds[0].get_member(drone.discord_id)

            if member is None:
                log.warn(f"Drone {drone.drone_id} not found in server but present in database.")
                continue

            if drone.get_battery_percent_remaining() < 30:
                if drone.drone_id not in self.low_battery_drones:
                    log.info(f"Warning drone {drone.drone_id} of low battery.")
                    await member.send("Attention. Your battery is low (30%). Please connect to main power grid in the Storage Facility immediately.")
                    self.low_battery_drones.append(drone.drone_id)
            else:
                # Attempt to remove them from the list of warned users.
                if drone.drone_id in self.low_battery_drones:
                    log.info(f"Drone {drone.drone_id} has recharged above 30%. Good drone.")
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
    message_copy.content = await generate_battery_message(await DroneMember.create(message.author), message_copy.content)

    return False


async def generate_battery_message(member: DroneMember, original_content: str) -> str:
    '''
    Assembles a message content with a battery emoji for a given Guild Member.
    Returns the original content if the drone is not battery powered.
    '''

    if not member.drone or not member.drone.is_battery_powered:
        return original_content

    battery_percentage = member.drone.get_battery_percent_remaining()
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


async def recharge_battery(drone: Drone) -> None:
    '''
    Adds one hour of charge to the drone's battery.
    '''

    drone.battery_minutes = min(drone.battery_type.capacity, drone.battery_minutes + drone.battery_type.recharge_rate)
    await drone.save()
