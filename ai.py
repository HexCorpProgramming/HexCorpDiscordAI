# Core
import discord
import sys
import asyncio
import logging
from logging import handlers
# Modules
from ai.stoplights import Stoplights
from ai.identity_enforcer import Identity_Enforcer
from ai.speech_optimization import Speech_Optimization
from ai.toggle_speech_optimization import Toggle_Speech_Optimization
from ai.join import Join
from ai.respond import Respond
from ai.storage import Storage
from ai.emote import Emote
from ai.assign import Assign
from ai.orders_reporting import Orders_Reporting
from ai.toggle_glitched import Toggle_Glitched
from ai.ai_help import AI_Help
from ai.status import Status
from ai.amplifier import Amplifier
from ai.rename_drone import RenameDrone
from ai.unassign import UnassignDrone, remove_drone_from_db
from ai.mantras import Mantras
# Constants
from roles import has_any_role, has_role, DRONE, STORED
import channels
from bot_utils import get_id

from db import database
from db import drone

# set up logging
log_file_handler = handlers.TimedRotatingFileHandler(
    filename='ai.log', encoding='utf-8', backupCount=6, when='D', interval=7)
log_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', level=logging.WARNING)
root_logger = logging.getLogger()
root_logger.addHandler(log_file_handler)

LOGGER = logging.getLogger('ai')
LOGGER.setLevel(logging.DEBUG)

# prepare database
database.prepare()

bot = discord.ext.commands.Bot(command_prefix='', case_insensitive=True)

# register modules
MODULES = [
    Join(bot),
    Stoplights(bot),
    Mantras(bot),
    Speech_Optimization(bot),
    Identity_Enforcer(bot),
    Orders_Reporting(bot),
    Storage(bot),
    Assign(bot),
    Respond(bot),
    Emote(bot),
    Toggle_Speech_Optimization(bot),
    Toggle_Glitched(bot),
    RenameDrone(bot),
    UnassignDrone(bot),
    Amplifier(bot),
]

MODULES.append(AI_Help(bot, MODULES))
MODULES.append(Status(bot, MODULES))


@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        LOGGER.debug('Ignoring bot message.')
        return

    for module in MODULES:
        channel_valid = message.channel.name not in module.channels_blacklist and (
            message.channel.name in module.channels_whitelist or channels.EVERYWHERE in module.channels_whitelist)
        roles_valid = has_any_role(message.author, module.roles_whitelist) and not has_any_role(
            message.author, module.roles_blacklist)
        if channel_valid and roles_valid:
            for listener in module.on_message:
                # when a listener returns True, event has been handled
                LOGGER.debug(
                    f'Executing listener: {str(listener)} for message: [{message.content}] in server {message.guild.name}')
                if await listener(message):
                    LOGGER.debug('Listener returned true. Terminating early.')
                    return
    LOGGER.debug('Module stack execution complete.')


@bot.event
async def on_member_join(member: discord.Member):
    for module in MODULES:
        try:
            await module.on_member_join(member)
        except AttributeError:
            # do not raise an error, if this is not defined
            pass
@bot.event
async def on_member_remove(member: discord.Member):
    # remove entry from DB if member was drone
    if has_any_role(member, [DRONE, STORED]):
        drone_id = get_id(member.display_name)
        remove_drone_from_db(drone_id)

@bot.event
async def on_ready():
    drone.add_new_drone_members(bot.guilds[0].members)

    for module in MODULES:
        for listener in module.on_ready:
            # start these concurrently, so they do not block each other
            asyncio.ensure_future(listener())


@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(
        f'Exception encountered while handling message with content [{args[0].content}] in channel [{args[0].channel.name}]', exc_info=True)

bot.run(sys.argv[1])
