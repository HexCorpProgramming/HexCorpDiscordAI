# Core
import discord
import sys
import asyncio
import logging
from logging import handlers
# Modules
import ai.stoplights as stoplights
import ai.identity_enforcement as identity_enforcement
import ai.speech_optimization as speech_optimization
import ai.toggle_speech_optimization as speech_optimization_toggler
from ai.join import Join
from ai.respond import Respond
from ai.storage import Storage
import ai.emote as emote_handler
from ai.assign import Assign
from ai.orders_reporting import Orders_Reporting
from ai.toggle_glitched import Toggle_Glitched
from ai.ai_help import AI_Help
from ai.status import Status
import ai.amplifier as amplification_handler
from ai.rename_drone import RenameDrone
from ai.unassign import UnassignDrone, remove_drone_from_db
from ai.mantras import Mantra_Handler
# Constants
from roles import has_any_role, has_role, DRONE, STORED
import channels
from bot_utils import get_id
from resources import DRONE_AVATAR, ENFORCER_AVATAR, HIVE_MXTRESS_AVATAR, HEXCORP_AVATAR

from db import database
from db import drone_dao

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

bot = discord.ext.commands.Bot(command_prefix='hc!', case_insensitive=True)
bot.remove_command("help")

# Instance modules
mantra_handler = Mantra_Handler(bot)

# register modules
MODULES = [
    Join(bot),
    stoplights,
    speech_optimization,
    identity_enforcement,
    Orders_Reporting(bot),
    Storage(bot),
    Assign(bot),
    Respond(bot),
    emote_handler,
    Toggle_Glitched(bot),
    RenameDrone(bot),
    UnassignDrone(bot),
]

MODULES.append(AI_Help(bot, MODULES))
MODULES.append(Status(bot, MODULES))



@bot.command(aliases = ['big', 'emote'])
async def bigtext(context, sentence):
    '''
    Transforms small text into heckin' chonky text.
    '''
    await emote_handler.generate_big_text(context.channel, sentence)

@bot.command(brief = "Hive Mxtress", usage = "hc!amplify '[message]', #target-channel-as-mention, drones (one or more IDs).")
async def amplify(context, message: str, target_channel: discord.TextChannel, *drones):
    '''
    Allows the Hive Mxtress to speak through other drones.
    '''
    await amplification_handler.amplify_message(context, message, target_channel, drones)

@bot.command(aliases = ['optimize', 'toggle_speech_op', 'tso'], brief = "Hive Mxtress", usage = "hc!toggle_speech_optimization @drones (one or more mentions).")
async def toggle_speech_optimization(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users to toggle drone speech optimization.
    '''
    await speech_optimization_toggler.toggle(context, drones)

@bot.command(brief = "DroneOS")
async def add_trusted_user(context):
    return "Drone OS example command."

@bot.command()
async def help(context):
    
    commands_card = discord.Embed(color=0xff66ff, title="Common commands", description = "Here is a list of common commands server members can utilize.")
    commands_card.set_thumbnail(url = HEXCORP_AVATAR)

    droneOS_card = discord.Embed(color=0xff66ff, title="DroneOS commands", description = "This is a list of DroneOS commands used to alter and manipulate DroneOS drones.")
    droneOS_card.set_thumbnail(url = DRONE_AVATAR)

    Hive_Mxtress_card = discord.Embed(color=0xff66ff, title="Hive Mxtress commands", description = "Only the Hive Mxtress can use these commands. Behold the tools they have available with which to toy with you, cutie.")
    Hive_Mxtress_card.set_thumbnail(url = HIVE_MXTRESS_AVATAR)

    for command in bot.commands:

        command_name = command.name
        if len(command.aliases) != 0:
            command_name += " ("
            for alias in command.aliases:
                command_name += f"{alias}, "
            command_name = f"{command_name[:-2]})"

        command_description = command.help if command.help is not None else "A naughty dev drone forgot to add a command description."
        command_description += f"\n`{command.usage}`" if command.usage is not None else "\n`No usage string available.`"

        if command.brief == "Hive Mxtress":

            Hive_Mxtress_card.add_field(name=command_name, value=command_description, inline=False)
        elif command.brief == "DroneOS":
            droneOS_card.add_field(name=command_name, value=command_description, inline=False)
        else:
            commands_card.add_field(name=command_name, value=command_description, inline=False)

    await context.send(embed=commands_card)
    await context.send(embed=droneOS_card)
    await context.send(embed=Hive_Mxtress_card)

@bot.command(brief = "Hive Mxtress")
async def repeat(context, *messages):
    await mantra_handler.update_mantra(context.message, messages)

@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        return

    LOGGER.info("Checking for stoplights.")

    #Check for stoplights
    if await stoplights.check_for_stoplights(message):
        return #Don't alter the message if it contains a stoplight.

    LOGGER.info("Checking for speech optimization.")

    #Check for speech optimization
    if await speech_optimization.optimize_speech(message):
        return #Message has been deleted or status code has been proxied.

    LOGGER.info("Checking for identity enforcement.")

    #Enforce identity if in Hive
    await identity_enforcement.enforce_identity(message)

    LOGGER.info("Processing additional commands.")

    #Finally, process additional commands where applicable
    await bot.process_commands(message)

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
    drone_dao.add_new_drone_members(bot.guilds[0].members)
    await mantra_handler.load_mantra()


@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(
        f'Exception encountered while handling message with content [{args[0].content}] in channel [{args[0].channel.name}]', exc_info=True)

bot.run(sys.argv[1])
