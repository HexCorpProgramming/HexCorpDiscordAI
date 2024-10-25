from pathlib import Path
from collections.abc import Callable, Coroutine
from typing import Any, List
from discord import Embed, Guild, Message
from discord.ext.commands import Cog, command, Context
import re
from src.bot_utils import channels_only
from src.log import log
from src.db.data_objects import Drone
from src.roles import has_role, DRONE

from src.bot_utils import COMMAND_PREFIX
from src.channels import BOT_DEV_COMMS
from src.resources import DRONE_AVATAR, HEXCORP_AVATAR, HIVE_MXTRESS_AVATAR

ListenerType = Callable[[Message, Any | None], Coroutine[Any, Any, bool]]


class StatusCog(Cog):
    '''
    The command handler for the "ai_status" command.
    '''

    def __init__(self, message_listeners: List[ListenerType]):
        self.message_listeners = message_listeners

    @channels_only(BOT_DEV_COMMS)
    @command(usage=f'{COMMAND_PREFIX}ai_status')
    async def ai_status(self, context: Context):
        '''
        A debug command, that displays information about the AI.
        '''

        log.info('Reporting bot status')

        await report_status(context, self.message_listeners)
        await report_drones(context)
        await report_drone_validation(context)


def read_version() -> str:
    '''
    Read and return the currently checked-out branch from Git.

    Returns an error message on failure.
    '''

    try:
        return Path('.git/HEAD').read_text()
    except:  # noqa: E722
        return '[unable to read version information]'


def get_list_of_commands(context: Context):
    '''
    Get a list of all the commands available on the bot.
    '''

    return sorted([command.name for command in context.bot.commands])


def get_list_of_listeners(listeners: List[ListenerType]):
    '''
    Get a list of all the message listener function names.
    '''

    return sorted([listener.__name__ for listener in listeners])


async def report_status(context: Context, listeners: List[ListenerType]) -> None:
    '''
    Creates an embed with some debug information about the AI.
    '''

    embed = Embed(title='AI status report', description='HexCorp Mxtress AI online', color=0xff66ff)
    embed.set_thumbnail(url=HEXCORP_AVATAR)

    embed.add_field(name='deployed commit', value=read_version(), inline=False)
    embed.add_field(name='registered commands', value=get_list_of_commands(context), inline=False)
    embed.add_field(name='message listeners', value=get_list_of_listeners(listeners), inline=False)

    await context.send(embed=embed)


async def report_drones(context: Context) -> None:
    '''
    Send status information about drones in the database.
    '''

    embed = Embed(title='Drone status report', description='Registered Entities', color=0xff66ff)
    embed.set_thumbnail(url=HIVE_MXTRESS_AVATAR)

    drones = await Drone.all()
    status_columns = {
        'optimized': 'Optimized',
        'glitched': 'Glitched',
        'id_prepending': 'ID Prepending',
        'identity_enforcement': 'Identity Enforced',
        'third_person_enforcement': 'Third Person Enforced',
        'can_self_configure': 'Self Configures',
        'is_battery_powered': 'Battery Powered ',
        'free_storage': 'Free Storage',
    }

    for drone in drones:
        status: List[str] = []

        for column in status_columns:
            if getattr(drone, column):
                if column == 'is_battery_powered':
                    status.append(status_columns[column] + str(drone.get_battery_percent_remaining()) + '%')
                else:
                    status.append(status_columns[column])

        member = context.guild.get_member(drone.discord_id)
        embed.add_field(name='Name', value=member.display_name if member else f'[Missing: {drone.drone_id}]', inline=True)
        embed.add_field(name='Discord ID', value=drone.discord_id, inline=True)
        embed.add_field(name='Status', value=', '.join(status), inline=True)

    await context.send(embed=embed)


async def find_missing_members(guild: Guild) -> List[str]:
    '''
    Find the Drone IDs of any drones that are in the databse but not on the server.
    '''

    drones = await Drone.all()
    missing_drones: List[str] = []

    for drone in drones:
        member = guild.get_member(drone.discord_id)

        if member is None:
            missing_drones.append(drone.drone_id)

    return missing_drones


async def find_mismatched_drones(guild: Guild) -> List[str]:
    '''
    Find drones whose name does not match their ID.
    '''

    mismatches: List[str] = []
    id_regex = re.compile(r'.-Drone #(\d{4})')

    for member in guild.members:
        drone = await Drone.find(discord_id=member.id)
        match = id_regex.match(member.display_name)

        if drone is None or match is None:
            continue

        id = match.group(1)

        if id != drone.drone_id:
            mismatches.append(member.display_name + ' registered as ' + id)

    return mismatches


async def find_missing_records(guild: Guild) -> List[str]:
    '''
    Find members with the Drone role that are not in the database.
    '''

    missing_records: List[str] = []

    for member in guild.members:
        if not has_role(member, DRONE):
            continue

        drone = await Drone.find(discord_id=member.id)

        if drone is None:
            missing_records.append(member.display_name)

    return missing_records


async def report_drone_validation(context: Context) -> None:
    '''
    Send debug information about drones in the database.
    '''

    embed = Embed(title='Drone validation report', description='Glitched Entities', color=0xff66ff)
    embed.set_thumbnail(url=DRONE_AVATAR)

    missing_members = await find_missing_members(context.guild)
    mismatched_ids = await find_mismatched_drones(context.guild)
    missing_records = await find_missing_records(context.guild)

    embed.add_field(name='Drones missing from the server', value=', '.join(missing_members) if len(missing_members) else 'None', inline=False)
    embed.add_field(name='Drones with mismatched IDs', value=', '.join(mismatched_ids) if len(mismatched_ids) else 'None', inline=False)
    embed.add_field(name=f'Members with the {DRONE} role not in the database', value=', '.join(missing_records) if len(missing_records) else 'None', inline=False)

    await context.send(embed=embed)
