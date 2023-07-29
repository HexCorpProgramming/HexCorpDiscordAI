import logging
import random
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Union
from uuid import uuid4

import discord
from discord.ext.commands import Cog, Greedy, command, dm_only, guild_only
from discord.utils import get

import src.webhook as webhook
from src.ai.commands import DroneMemberConverter, NamedParameterConverter
from src.ai.identity_enforcement import identity_enforcable
from src.ai.storage import release
from src.bot_utils import COMMAND_PREFIX, get_id
from src.channels import OFFICE
from src.db.data_objects import Timer
from src.db.drone_dao import (can_self_configure, delete_drone_by_drone_id,
                              fetch_drone_with_drone_id, fetch_drone_with_id,
                              get_trusted_users, is_battery_powered,
                              is_glitched, is_identity_enforced, is_optimized,
                              is_prepending_id, rename_drone_in_db,
                              set_battery_minutes_remaining,
                              update_droneOS_parameter)
from src.db.drone_order_dao import delete_drone_order_by_drone_id
from src.db.storage_dao import delete_storage_by_target_id
from src.db.timer_dao import (delete_timers_by_drone_id,
                              delete_timers_by_drone_id_and_mode, insert_timer)
from src.display_names import update_display_name
from src.id_converter import convert_id_to_member
from src.resources import (BRIEF_DM_ONLY, BRIEF_DRONE_OS, BRIEF_HIVE_MXTRESS,
                           DRONE_AVATAR, HIVE_MXTRESS_USER_ID,
                           MAX_BATTERY_CAPACITY_MINS)
from src.roles import (ADMIN, ASSOCIATE, BATTERY_DRAINED, BATTERY_POWERED,
                       DRONE, GLITCHED, HIVE_MXTRESS, ID_PREPENDING,
                       IDENTITY_ENFORCEMENT, MODERATION_ROLES,
                       SPEECH_OPTIMIZATION, STORED, has_any_role, has_role)

LOGGER = logging.getLogger('ai')

MINUTES_PARAMETER = "minutes"


class DroneConfigurationCog(Cog):

    @guild_only()
    @command(brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}emergency_release 9813')
    async def emergency_release(self, context, drone_id: str):
        '''
        Lets moderators disable all DroneOS restrictions currently active on a drone.
        '''
        if has_any_role(context.author, MODERATION_ROLES):
            await emergency_release(context, drone_id)

    @dm_only()
    @command(brief=[BRIEF_DRONE_OS, BRIEF_DM_ONLY], usage=f"{COMMAND_PREFIX}unassign")
    async def unassign(self, context):
        '''
        Allows a drone to go back to the status of an Associate.
        '''
        await unassign_drone(context.bot.guilds[0].get_member(context.author.id))

    @guild_only()
    @command(brief=[BRIEF_HIVE_MXTRESS], usage=f'{COMMAND_PREFIX}rename 1234 3412')
    async def rename(self, context, old_id, new_id):
        '''
        Allows the Hive Mxtress to change the ID of a drone.
        '''
        if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
            await rename_drone(context, old_id, new_id)

    @guild_only()
    @command(aliases=['tid'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_id_prepending 5890 9813')
    async def toggle_id_prepending(self, context, drones: Greedy[Union[discord.Member, DroneMemberConverter]], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Allows the Hive Mxtress or trusted users to enforce mandatory ID prepending upon specified drones.
        '''
        await toggle_parameter(context,
                               drones,
                               "id_prepending",
                               get(context.guild.roles, name=ID_PREPENDING),
                               is_prepending_id,
                               lambda: "ID prepending is now mandatory.",
                               lambda minutes: f"ID prepending is now mandatory for {minutes} minute(s).",
                               lambda: "Prepending? More like POST pending now that that's over! Haha!" if random.randint(1, 100) == 66 else "ID prependment policy relaxed.",
                               minutes)

    @guild_only()
    @command(aliases=['optimize', 'toggle_speech_op', 'tso'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_speech_optimization 5890 9813')
    async def toggle_speech_optimization(self, context, drones: Greedy[Union[discord.Member, DroneMemberConverter]], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone speech optimization.
        '''
        await toggle_parameter(context,
                               drones,
                               "optimized",
                               get(context.guild.roles, name=SPEECH_OPTIMIZATION),
                               is_optimized,
                               lambda: "Speech optimization is now active.",
                               lambda minutes: f"Speech optimization is now active for {minutes} minute(s).",
                               lambda: "Speech optimization disengaged.",
                               minutes)

    @guild_only()
    @command(aliases=['tei'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_enforce_identity 5890 9813')
    async def toggle_enforce_identity(self, context, drones: Greedy[Union[discord.Member, DroneMemberConverter]], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone identity enforcement.
        '''
        await toggle_parameter(context,
                               drones,
                               "identity_enforcement",
                               get(context.guild.roles, name=IDENTITY_ENFORCEMENT),
                               is_identity_enforced,
                               lambda: "Identity enforcement is now active.",
                               lambda minutes: f"Identity enforcement is now active for {minutes} minute(s).",
                               lambda: "Identity enforcement disengaged.",
                               minutes)

    @guild_only()
    @command(aliases=['glitch', 'tdg'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_drone_glitch 9813 3287')
    async def toggle_drone_glitch(self, context, drones: Greedy[Union[discord.Member, DroneMemberConverter]], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone glitch levels.
        '''
        await toggle_parameter(context,
                               drones,
                               "glitched",
                               get(context.guild.roles, name=GLITCHED),
                               is_glitched,
                               lambda: "Uh.. it’s probably not a problem.. probably.. but I’m showing a small discrepancy in... well, no, it’s well within acceptable bounds again. Sustaining sequence." if random.randint(1, 100) == 66 else "Drone corruption at un̘͟s̴a̯f̺e͈͡ levels.",
                               lambda minutes: f"Drone corruption scheduled to reflect un̘͟s̴a̯f̺e͈͡ levels for {minutes} minute(s).",
                               lambda: "Drone corruption at acceptable levels.",
                               minutes)

    @guild_only()
    @command(aliases=['battery', 'tbp'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_battery_power 0001')
    async def toggle_battery_power(self, context, drones: Greedy[Union[discord.Member, DroneMemberConverter]], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle whether or not a drone is battery powered.
        '''
        await toggle_parameter(context,
                               drones,
                               "is_battery_powered",
                               get(context.guild.roles, name=BATTERY_POWERED),
                               is_battery_powered,
                               lambda: "Drone disconnected from HexCorp power grid. Auxiliary power active.",
                               lambda minutes: f"Drone disconnected from HexCorp power grid for {minutes} minutes.",
                               lambda: "Drone reconnected to HexCorp power grid.",
                               minutes)
        # Additionally, reset the battery of any drone regardless of whether or not it's being toggled on or off.
        # And remove drained role if added.
        for drone in drones:
            set_battery_minutes_remaining(member=drone, minutes=MAX_BATTERY_CAPACITY_MINS)
            await drone.remove_roles(get(context.guild.roles, name=BATTERY_DRAINED))


async def rename_drone(context, old_id: str, new_id: str):
    if len(old_id) != 4 or len(new_id) != 4:
        return
    if not old_id.isnumeric() or not new_id.isnumeric():
        return

    LOGGER.info("IDs to rename drone to and from are both valid.")

    # check for collisions
    collision = fetch_drone_with_drone_id(new_id)
    if collision is None:
        drone = fetch_drone_with_drone_id(old_id)
        member = context.guild.get_member(drone.id)
        rename_drone_in_db(old_id, new_id)
        await member.edit(nick=f'⬡-Drone #{new_id}')
        await update_display_name(member)
        await context.send(f"Successfully renamed drone {old_id} to {new_id}.")
    else:
        await context.send(f"ID {new_id} already in use.")


async def unassign_drone(target: discord.Member):
    drone = fetch_drone_with_id(target.id)
    guild = target.guild
    # check for existence
    if drone is None:
        await target.send("You are not a drone. Can not unassign.")
        return

    await target.edit(nick=drone.associate_name)
    await target.remove_roles(get(guild.roles, name=DRONE), get(guild.roles, name=STORED), get(guild.roles, name=SPEECH_OPTIMIZATION), get(guild.roles, name=GLITCHED), get(guild.roles, name=ID_PREPENDING), get(guild.roles, name=IDENTITY_ENFORCEMENT), get(guild.roles, name=BATTERY_POWERED), get(guild.roles, name=BATTERY_DRAINED))
    await target.add_roles(get(guild.roles, name=ASSOCIATE))

    # remove from DB
    remove_drone_from_db(drone.drone_id)
    await target.send(f"Drone with ID {drone.drone_id} unassigned.")


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    delete_drone_order_by_drone_id(drone_id)
    delete_storage_by_target_id(drone_id)
    delete_drone_by_drone_id(drone_id)
    delete_timers_by_drone_id(drone_id)


async def emergency_release(context, drone_id: str):
    drone_member = convert_id_to_member(context.guild, drone_id)

    if drone_member is None:
        await context.channel.send(f"No drone with ID {drone_id} found.")
        return

    await release(context, drone_id)

    update_droneOS_parameter(drone_member, "id_prepending", False)
    update_droneOS_parameter(drone_member, "optimized", False)
    update_droneOS_parameter(drone_member, "identity_enforcement", False)
    update_droneOS_parameter(drone_member, "glitched", False)
    update_droneOS_parameter(drone_member, "is_battery_powered", False)
    await drone_member.remove_roles(get(context.guild.roles, name=SPEECH_OPTIMIZATION), get(context.guild.roles, name=GLITCHED), get(context.guild.roles, name=ID_PREPENDING), get(context.guild.roles, name=IDENTITY_ENFORCEMENT), get(context.guild.roles, name=BATTERY_POWERED), get(context.guild.roles, name=BATTERY_DRAINED))
    await update_display_name(drone_member)

    await context.channel.send(f"Restrictions disabled for drone {drone_id}.")


def can_toggle_permissions_for(toggling_user: discord.Member,
                               toggled_user: discord.Member
                               ) -> bool:
    trusted_users = get_trusted_users(toggled_user.id)
    if toggling_user.id == HIVE_MXTRESS_USER_ID:
        return True
    if toggling_user.id in trusted_users:
        return True
    if toggling_user.id == toggled_user.id:
        return can_self_configure(toggled_user)
    return False


def is_configured(drone_member: discord.Member) -> bool:
    toggles = (is_prepending_id,
               is_optimized,
               is_identity_enforced,
               is_glitched,
               )
    return any(is_toggled(drone_member) for is_toggled in toggles)


async def toggle_parameter(context,
                           drones: List[discord.Member],
                           toggle_column: str,
                           role: discord.Role,
                           is_toggle_activated: Callable[[discord.Member], bool],
                           toggle_on_message: Callable[[], str],
                           toggle_on_timed_message: Callable[[int], str],
                           toggle_off_message: Callable[[], str],
                           minutes: Optional[int] = 0):
    channel_webhook = await webhook.get_webhook_for_channel(context.channel)

    for drone in drones:
        if can_toggle_permissions_for(context.author, drone):
            message = ""
            if is_toggle_activated(drone):
                update_droneOS_parameter(drone, toggle_column, False)
                await drone.remove_roles(role)
                message = toggle_off_message()

                set_can_self_configure(drone)

                # remove any open timers for this mode
                delete_timers_by_drone_id_and_mode(fetch_drone_with_id(drone.id).drone_id, toggle_column)

            else:
                update_droneOS_parameter(drone, toggle_column, True)
                await drone.add_roles(role)
                message = toggle_on_message()

                configured_by_self = (drone.id == context.author.id)
                update_droneOS_parameter(drone, "can_self_configure", configured_by_self)

                # create a new timer
                if minutes > 0:
                    end_time = str(datetime.now() + timedelta(minutes=minutes))
                    timer = Timer(str(uuid4()), fetch_drone_with_id(drone.id).drone_id, toggle_column, end_time)
                    insert_timer(timer)
                    message = toggle_on_timed_message(minutes)
                    LOGGER.info(f"Created a new config timer for {drone.display_name} toggling on {toggle_column} elapsing at {end_time}")

            is_admin = has_role(drone, ADMIN)
            if await update_display_name(drone) and not is_admin:
                # Display name has been updated, get the new drone object with updated display name.
                drone = context.guild.get_member(drone.id)
            await webhook.proxy_message_by_webhook(message_content=f'{get_id(drone.display_name)} :: {message}',
                                                   message_username=drone.display_name,
                                                   message_avatar=drone.display_avatar.url if not identity_enforcable(drone, channel=context.channel) else DRONE_AVATAR,
                                                   webhook=channel_webhook)


def set_can_self_configure(drone: discord.Member):
    still_configured = is_configured(drone)
    if not still_configured:
        update_droneOS_parameter(drone, "can_self_configure", True)
