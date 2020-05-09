# Core
import discord
import sys
import asyncio
import logging
# Modules
from identity_enforcer import Identity_Enforcer
from speech_optimization import Speech_Optimization
from toggle_speech_optimization import Toggle_Speech_Optimization
from join import Join
from respond import Respond
from storage import Storage
from emote import Emote
from assign import Assign
from orders_reporting import Orders_Reporting
from ai_help import AI_Help
from status_code import StatusCode
# Constants
from roles import has_any_role
import channels

# set up logging
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
root_logger = logging.getLogger()
root_file_handler = logging.FileHandler(
    filename='ai.log', encoding='utf-8', mode='a')
root_file_handler.setLevel(logging.WARNING)
root_file_handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
root_logger.addHandler(root_file_handler)

LOGGER = logging.getLogger('ai')
LOGGER.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(
    filename='ai.log', encoding='utf-8', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
LOGGER.addHandler(file_handler)




bot = discord.ext.commands.Bot(command_prefix='', case_insensitive=True)

# register modules
MODULES = [
    Join(bot),
    Speech_Optimization(bot),
    Identity_Enforcer(bot),
    Orders_Reporting(bot),
    Storage(bot),
    Assign(bot),
    Respond(bot),
    Emote(bot),
    Toggle_Speech_Optimization(bot),
    StatusCode(bot),
]

MODULES = MODULES + [AI_Help(bot, MODULES)]


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
async def on_ready():
    for module in MODULES:
        for listener in module.on_ready:
            # start these concurrently, so they do not block each other
            asyncio.ensure_future(listener())


@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(
        f'Exception encountered while handling message with content [{args[0].content}] in channel [{args[0].channel.name}]', exc_info=True)

bot.run(sys.argv[1])
