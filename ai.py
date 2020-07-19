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
import ai.join as join_handler
from ai.respond import Respond
import ai.storage as storage
import ai.emote as emote_handler
from ai.assign import Assign
import ai.orders_reporting as orders_reporting
from ai.toggle_glitched import Toggle_Glitched
from ai.ai_help import AI_Help
from ai.status import Status
import ai.amplifier as amplification_handler
from ai.rename_drone import RenameDrone
from ai.unassign import unassign_drone, remove_drone_from_db
from ai.mantras import Mantra_Handler
from ai.toggle_role import toggle_role
# Constants
from roles import has_any_role, has_role, DRONE, STORED, SPEECH_OPTIMIZATION, GLITCHED, HIVE_MXTRESS
from channels import STORAGE_FACILITY, DRONE_HIVE_CHANNELS, OFFICE, ORDERS_REPORTING, INITIATION
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

#Run-forever checkers.
checking_for_completed_orders = False
reporting_storage = False
checking_for_stored_drones_to_release = False

# register modules
MODULES = [
    stoplights,
    speech_optimization,
    identity_enforcement,
    Assign(bot),
    Respond(bot),
    emote_handler,
    Toggle_Glitched(bot),
    RenameDrone(bot),
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
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await amplification_handler.amplify_message(context, message, target_channel, drones)

@bot.command(aliases = ['optimize', 'toggle_speech_op', 'tso'], brief = "Hive Mxtress", usage = "hc!toggle_speech_optimization @drones (one or more mentions).")
async def toggle_speech_optimization(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone speech optimization.
    '''
    await toggle_role(context, drones, SPEECH_OPTIMIZATION)

@bot.command(aliaes = ['glitch', 'tdg'], brief = "Hive Mxtress", usage = "hc!toggle_drone_glitch @drones (one or more mentions).")
async def toggle_drone_glitch(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone glitch levels.
    '''
    await toggle_role(context, drones, GLITCHED)

@bot.command(usage = "hc!unassign 0000")
async def unassign(context, drone):
    await unassign(context, drone)

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

@bot.command(aliases = ["report_order"], usage = "hc!report '[protocol name]' [time] (max 120 minutes.)")
async def report(context, protocol_name: str, protocol_time: str):
    if context.channel.name == ORDERS_REPORTING:
        await orders_reporting.report_order(context, protocol_name, int(protocol_time))

@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        return

    if message.channel.name == INITIATION:
        LOGGER.info("Checking for initiate consent.")
        join_handler.check_for_consent(message)
        return

    LOGGER.info("Checking for stoplights.")
    if await stoplights.check_for_stoplights(message):
        return #Don't alter the message if it contains a stoplight.

    LOGGER.info("Checking for speech optimization.")
    if await speech_optimization.optimize_speech(message):
        return #Message has been deleted or status code has been proxied.
    
    if message.channel.name in DRONE_HIVE_CHANNELS:
        LOGGER.info("Checking for identity enforcement.")
        await identity_enforcement.enforce_identity(message)

    if message.channel.name == STORAGE_FACILITY:
        LOGGER.info("Checking for storage requests.")
        await storage.store_drone(message)
        return #No need to process additional commands in the storage facility.

    LOGGER.info("Processing additional commands.")
    await bot.process_commands(message)

@bot.event
async def on_member_join(member: discord.Member):
    join_handler.on_member_join(member)

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

    if not checking_for_completed_orders:
        asyncio.ensure_future(orders_reporting.check_for_completed_orders(bot))

    if not reporting_storage:
        asyncio.ensure_future(storage.report_storage(bot))

    if not checking_for_stored_drones_to_release:
        asyncio.ensure_future(storage.release_timed(bot))

@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(
        f'Exception encountered while handling message with content [{args[0].content}] in channel [{args[0].channel.name}]', exc_info=True)

bot.run(sys.argv[1])
