import random
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional
from uuid import uuid4

import discord
from discord.ext.commands import Cog, Context, Greedy, guild_only, UserInputError

import src.webhook as webhook
from src.ai.commands import NamedParameterConverter
from src.ai.storage import release
from src.bot_utils import channels_only, command, COMMAND_PREFIX, dm_only, fetch, hive_mxtress_only, moderator_only
from src.channels import OFFICE
from src.db.data_objects import Timer
from src.db.drone_dao import delete_timers_by_id_and_mode
from src.resources import BRIEF_DRONE_OS
from src.roles import (ADMIN, ASSOCIATE, BATTERY_DRAINED, BATTERY_POWERED,
                       DRONE, FREE_STORAGE, GLITCHED, ID_PREPENDING,
                       IDENTITY_ENFORCEMENT, SPEECH_OPTIMIZATION, STORED,
                       THIRD_PERSON_ENFORCEMENT, has_role)
from src.log import log
from src.drone_member import DroneMember
from src.db.data_objects import Drone

MINUTES_PARAMETER = "minutes"


class DroneConfigurationCog(Cog):
    '''
    Commands relating to DroneOS.
    '''

    @guild_only()
    @moderator_only()
    @command(brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}emergency_release 9813')
    async def emergency_release(self, context, member: DroneMember):
        '''
        Lets moderators disable all DroneOS restrictions currently active on a drone.
        '''

        await emergency_release(context, member)

    @dm_only()
    @command(brief=[BRIEF_DRONE_OS], usage=f"{COMMAND_PREFIX}unassign")
    async def unassign(self, context: Context):
        '''
        Allows a drone to go back to the status of an Associate.
        '''

        guild = context.message.guild if context.message.guild else context.bot.guilds[0]
        await unassign_drone(await DroneMember.load(guild, discord_id=context.author.id))

    @dm_only()
    @command(aliases=['free_storage', 'tfs'], brief=[BRIEF_DRONE_OS], usage=f"{COMMAND_PREFIX}toggle_free_storage")
    async def toggle_free_storage(self, context):
        '''
        Allows a drone to choose whether to be stored by anyone, or just its trusted users and the Hive Mxtress. Defaults to trusted users only.
        '''
        await toggle_free_storage(context.bot.guilds[0].get_member(context.author.id))

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(briefusage=f'{COMMAND_PREFIX}rename 1234 3412')
    async def rename(self, context, old_id, new_id):
        '''
        Allows the Hive Mxtress to change the ID of a drone.
        '''

        await rename_drone(context, old_id, new_id)

    @guild_only()
    @command(aliases=['tid'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_id_prepending 5890 9813')
    async def toggle_id_prepending(self, context, members: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Allows the Hive Mxtress or trusted users to enforce mandatory ID prepending upon specified drones.
        '''
        await toggle_parameter(context,
                               members,
                               "id_prepending",
                               fetch(context.guild.roles, name=ID_PREPENDING),
                               lambda: "ID prepending is now mandatory.",
                               lambda minutes: f"ID prepending is now mandatory for {minutes} minute(s).",
                               lambda: "Prepending? More like POST pending now that that's over! Haha!" if random.randint(1, 100) == 66 else "ID prependment policy relaxed.",
                               minutes)

    @guild_only()
    @command(aliases=['optimize', 'toggle_speech_op', 'tso'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_speech_optimization 5890 9813')
    async def toggle_speech_optimization(self, context, members: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone speech optimization.
        '''
        await toggle_parameter(context,
                               members,
                               "optimized",
                               fetch(context.guild.roles, name=SPEECH_OPTIMIZATION),
                               lambda: "Speech optimization is now active.",
                               lambda minutes: f"Speech optimization is now active for {minutes} minute(s).",
                               lambda: "Speech optimization disengaged.",
                               minutes)

    @guild_only()
    @command(aliases=['tei'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_enforce_identity 5890 9813')
    async def toggle_enforce_identity(self, context, members: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone identity enforcement.
        '''

        latest_join = datetime.now(timezone.utc) - timedelta(weeks=2)
        permitted_members = [m for m in members if m.joined_at <= latest_join]
        forbidden_members = [m for m in members if m.joined_at > latest_join]

        if len(forbidden_members):
            if len(forbidden_members) == 1:
                text = 'Target ' + forbidden_members[0].display_name + ' has'
            else:
                text = 'Targets ' + ', '.join([m.display_name for m in forbidden_members]) + ' have'

            await context.reply(text + ' not been on the server for more than 2 weeks. Can not enforce identity.')

        if len(permitted_members):
            await toggle_parameter(
                context,
                permitted_members,
                "identity_enforcement",
                fetch(context.guild.roles, name=IDENTITY_ENFORCEMENT),
                lambda: "Identity enforcement is now active.",
                lambda minutes: f"Identity enforcement is now active for {minutes} minute(s).",
                lambda: "Identity enforcement disengaged.",
                minutes
            )

    @guild_only()
    @command(aliases=['tet'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_enforce_third_person 5890 9813')
    async def toggle_enforce_third_person(self, context, drones: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle third person enforcement.
        '''

        await toggle_parameter(context,
                               drones,
                               'third_person_enforcement',
                               fetch(context.guild.roles, name=THIRD_PERSON_ENFORCEMENT),
                               lambda: "Third person enforcement is now active.",
                               lambda minutes: f"Third Person enforcement is now active for {minutes} minute(s).",
                               lambda: "Third person enforcement disengaged.",
                               minutes)

    @guild_only()
    @command(aliases=['glitch', 'tdg'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_drone_glitch 9813 3287')
    async def toggle_drone_glitch(self, context, drones: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle drone glitch levels.
        '''
        await toggle_parameter(context,
                               drones,
                               "glitched",
                               fetch(context.guild.roles, name=GLITCHED),
                               lambda: "Uh.. it’s probably not a problem.. probably.. but I’m showing a small discrepancy in... well, no, it’s well within acceptable bounds again. Sustaining sequence." if random.randint(1, 100) == 66 else "Drone corruption at un̘͟s̴a̯f̺e͈͡ levels.",
                               lambda minutes: f"Drone corruption scheduled to reflect un̘͟s̴a̯f̺e͈͡ levels for {minutes} minute(s).",
                               lambda: "Drone corruption at acceptable levels.",
                               minutes)

    @guild_only()
    @command(aliases=['battery', 'tbp'], brief=[BRIEF_DRONE_OS], usage=f'{COMMAND_PREFIX}toggle_battery_power 0001')
    async def toggle_battery_power(self, context, members: Greedy[DroneMember], minutes: NamedParameterConverter(MINUTES_PARAMETER, int) = 0):
        '''
        Lets the Hive Mxtress or trusted users toggle whether or not a drone is battery powered.
        '''
        await toggle_parameter(context,
                               members,
                               "is_battery_powered",
                               fetch(context.guild.roles, name=BATTERY_POWERED),
                               lambda: "Drone disconnected from HexCorp power grid. Auxiliary power active.",
                               lambda minutes: f"Drone disconnected from HexCorp power grid for {minutes} minutes.",
                               lambda: "Drone reconnected to HexCorp power grid.",
                               minutes)
        # Additionally, reset the battery of any drone regardless of whether or not it's being toggled on or off.
        # And remove drained role if added.
        for member in members:
            if not member.drone:
                continue

            member.drone.battery_minutes = member.drone.battery_type.capacity
            await member.drone.save()
            await member.remove_roles(fetch(context.guild.roles, name=BATTERY_DRAINED))


async def rename_drone(context, old_id: str, new_id: str):
    if len(old_id) != 4 or len(new_id) != 4:
        raise UserInputError('Drone IDs must be four digit numbers')

    if not old_id.isnumeric() or not new_id.isnumeric():
        raise UserInputError('Drone IDs must be four digit numbers')

    # check for collisions
    collision = await Drone.find(drone_id=new_id)

    if collision is None:
        drone_member = await DroneMember.load(context.guild, drone_id=old_id)
        drone_member.drone.drone_id = new_id
        await drone_member.drone.save()
        await drone_member.edit(nick=f'⬡-Drone #{new_id}')
        await drone_member.update_display_name()
        await context.send(f"Successfully renamed drone {old_id} to {new_id}.")
        log.info(f"Renamed drone {old_id} to {new_id}.")
    else:
        raise UserInputError(f"ID {new_id} already in use.")


async def unassign_drone(target: DroneMember):
    guild = target.guild

    # check for existence
    if target.drone is None:
        raise UserInputError("You are not a drone. Can not unassign.")

    await target.edit(nick=target.drone.associate_name)
    await target.remove_roles(fetch(guild.roles, name=DRONE), fetch(guild.roles, name=STORED), fetch(guild.roles, name=SPEECH_OPTIMIZATION), fetch(guild.roles, name=GLITCHED), fetch(guild.roles, name=ID_PREPENDING), fetch(guild.roles, name=IDENTITY_ENFORCEMENT), fetch(guild.roles, name=BATTERY_POWERED), fetch(guild.roles, name=BATTERY_DRAINED))
    await target.add_roles(fetch(guild.roles, name=ASSOCIATE))

    # remove from DB
    await target.drone.delete()

    log.info(f'Unassigned drone {target.drone.drone_id}')

    try:
        await target.send(f"Drone with ID {target.drone.drone_id} unassigned.")
    except Exception:
        # Sending will fail if target is a Discord bot.
        pass


async def emergency_release(context, drone_member: DroneMember):
    if drone_member.drone is None:
        raise UserInputError(f"Member {drone_member.display_name} is not a drone.")

    await release(context, drone_member)

    drone_member.drone.id_prepending = False
    drone_member.drone.optimized = False
    drone_member.drone.identity_enforcement = False
    drone_member.drone.third_person_enforcement = False
    drone_member.drone.glitched = False
    drone_member.drone.is_battery_powered = False
    drone_member.drone.can_self_configure = True
    await drone_member.drone.save()

    await drone_member.remove_roles(fetch(context.guild.roles, name=SPEECH_OPTIMIZATION), fetch(context.guild.roles, name=GLITCHED), fetch(context.guild.roles, name=ID_PREPENDING), fetch(context.guild.roles, name=IDENTITY_ENFORCEMENT), fetch(context.guild.roles, name=BATTERY_POWERED), fetch(context.guild.roles, name=BATTERY_DRAINED))
    await drone_member.update_display_name()

    await context.channel.send(f"Restrictions disabled for drone {drone_member.drone.drone_id}.")
    log.info(f'Emergency released drone {drone_member.drone.drone_id}')


async def toggle_parameter(context,
                           members: List[DroneMember],
                           toggle_column: str,
                           role: discord.Role,
                           toggle_on_message: Callable[[], str],
                           toggle_on_timed_message: Callable[[int], str],
                           toggle_off_message: Callable[[], str],
                           minutes: Optional[int] = 0):
    channel_webhook = await webhook.get_webhook_for_channel(context.channel)

    for member in members:
        if member.drone is None:
            continue

        # Check that the message author can configure the drone.
        if not member.drone.allows_configuration_by(context.author):
            continue

        message = ""

        if getattr(member.drone, toggle_column):
            setattr(member.drone, toggle_column, False)
            await member.remove_roles(role)
            message = toggle_off_message()

            if not member.drone.is_configured():
                # Restore the drone's ability to self-configure if they are no longer configured.
                member.drone.can_self_configure = True

            # remove any open timers for this mode
            await delete_timers_by_id_and_mode(member.id, toggle_column)

        else:
            setattr(member.drone, toggle_column, True)
            await member.add_roles(role)
            message = toggle_on_message()

            # Remove the drone's ability to self-configure if someone else is configuring them.
            member.drone.can_self_configure = (member.id == context.author.id)

            # create a new timer
            if minutes:
                end_time = datetime.now() + timedelta(minutes=minutes)
                timer = Timer(str(uuid4()), member.id, toggle_column, end_time)
                await timer.insert()
                message = toggle_on_timed_message(minutes)
                log.info(f"Created a new config timer for {member.display_name} toggling on {toggle_column} elapsing at {end_time}")

        await member.drone.save()

        is_admin = has_role(member, ADMIN)

        if await member.update_display_name() and not is_admin:
            # Display name has been updated, get the new drone object with updated display name.
            member = await DroneMember.create(context.guild.get_member(member.id))

        await webhook.proxy_message_by_webhook(message_content=f'{member.drone.drone_id} :: {message}',
                                               message_username=member.display_name,
                                               message_avatar=member.avatar_url(context.channel),
                                               webhook=channel_webhook)


async def set_can_self_configure(member: DroneMember):
    if not member.drone.is_configured():
        member.drone.can_self_configure = True
        member.drone.save()


async def toggle_free_storage(target: DroneMember):
    drone = target.drone
    guild = target.guild

    # check for existence
    if drone is None:
        raise UserInputError("You are not a drone. Cannot toggle this parameter.")

    if drone.free_storage:
        drone.free_storage = False
        await drone.save()
        await target.remove_roles(fetch(guild.roles, name=FREE_STORAGE))
        await target.send("Free storage disabled. You can now only be stored by trusted users or the Hive Mxtress.")
        log.info('Free storage disabled')
    else:
        drone.free_storage = True
        await drone.save()
        await target.add_roles(fetch(guild.roles, name=FREE_STORAGE))
        await target.send("Free storage enabled. You can now be stored by anyone.")
        log.info('Free storage enabled')
