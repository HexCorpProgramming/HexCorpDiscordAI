# Core
import discord
import sys
import asyncio
import logging
from logging import handlers
from discord.ext.commands import Bot
# Modules
import ai.stoplights as stoplights
import ai.identity_enforcement as identity_enforcement
import ai.speech_optimization as speech_optimization
import ai.join as join
import ai.respond as respond
import ai.storage as storage
import ai.emote as emote
import ai.assign as assign
import ai.orders_reporting as orders_reporting
import ai.status as status
import ai.amplifier as amplifier
import ai.drone_management as drone_management
import ai.toggle_role as toggle_role
from ai.mantras import Mantra_Handler
# Utils
from bot_utils import get_id
import id_converter
# Database
from db import database
from db import drone_dao
# Constants
from roles import has_any_role, has_role, DRONE, STORED, SPEECH_OPTIMIZATION, GLITCHED, HIVE_MXTRESS
from channels import DRONE_HIVE_CHANNELS, OFFICE, ORDERS_REPORTING, REPETITIONS, BOT_DEV_COMMS
from resources import DRONE_AVATAR, HIVE_MXTRESS_AVATAR, HEXCORP_AVATAR

# Logging setup
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

# Prepare database
database.prepare()

# Setup bot
bot = Bot(command_prefix='hc!', case_insensitive=True)
bot.remove_command("help")

# Instance modules
mantra_handler = Mantra_Handler(bot)

# Run-forever checkers.
checking_for_completed_orders = False
reporting_storage = False
checking_for_stored_drones_to_release = False

# Register message listeners.
message_listeners = [
    join.check_for_consent,
    assign.check_for_assignment_message,
    stoplights.check_for_stoplights,
    speech_optimization.optimize_speech,
    respond.respond_to_question,
    identity_enforcement.enforce_identity,
    storage.store_drone,
]


@bot.command(aliases=['big', 'emote'])
async def bigtext(context, sentence):
    '''
    Transforms small text into heckin' chonky text.
    '''
    if context.channel.name not in DRONE_HIVE_CHANNELS:
        if (reply := emote.generate_big_text(context.channel, sentence)):
            await context.send(reply)


@bot.command(brief="Hive Mxtress", usage="hc!amplify '[message]', #target-channel-as-mention, drones (one or more IDs).")
async def amplify(context, message: str, target_channel: discord.TextChannel, *drones):
    '''
    Allows the Hive Mxtress to speak through other drones.
    '''
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await amplifier.amplify_message(context, message, target_channel, drones)


@bot.command(aliases=['optimize', 'toggle_speech_op', 'tso'], brief="Hive Mxtress", usage="hc!toggle_speech_optimization @drones (one or more mentions).")
async def toggle_speech_optimization(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone speech optimization.
    '''

    member_drones = id_converter.convert_ids_to_members(context.guild, drones)

    if has_role(context.author, HIVE_MXTRESS):
        await toggle_role.toggle_role(context, member_drones + context.message.mentions, SPEECH_OPTIMIZATION)


@bot.command(aliases=['glitch', 'tdg'], brief="Hive Mxtress", usage="hc!toggle_drone_glitch @drones (one or more mentions).")
async def toggle_drone_glitch(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone glitch levels.
    '''

    member_drones = id_converter.convert_ids_to_members(context.guild, drones)

    if has_role(context.author, HIVE_MXTRESS):
        await toggle_role.toggle_role(context, member_drones + context.message.mentions, GLITCHED)


@bot.command(usage="hc!unassign 0000")
async def unassign(context, drone):
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await drone_management.unassign_drone(context, drone)


@bot.command()
async def rename(context, old_id, new_id):
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await drone_management.rename_drone(context, old_id, new_id)


@bot.command(brief="DroneOS")
async def add_trusted_user(context):
    return "Drone OS example command."


@bot.command()
async def help(context):
    commands_card = discord.Embed(color=0xff66ff, title="Common commands", description="Here is a list of common commands server members can utilize.")
    commands_card.set_thumbnail(url=HEXCORP_AVATAR)

    droneOS_card = discord.Embed(color=0xff66ff, title="DroneOS commands", description="This is a list of DroneOS commands used to alter and manipulate DroneOS drones.")
    droneOS_card.set_thumbnail(url=DRONE_AVATAR)

    Hive_Mxtress_card = discord.Embed(color=0xff66ff, title="Hive Mxtress commands", description="Only the Hive Mxtress can use these commands. Behold the tools they have available with which to toy with you, cutie.")
    Hive_Mxtress_card.set_thumbnail(url=HIVE_MXTRESS_AVATAR)

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


@bot.command(brief="Hive Mxtress")
async def repeat(context, *messages):
    if context.channel.name == REPETITIONS and has_role(context.author, HIVE_MXTRESS):
        await mantra_handler.update_mantra(context.message, messages)


@bot.command(aliases=["report_order"], usage="hc!report '[protocol name]' [time] (max 120 minutes.)")
async def report(context, protocol_name: str, protocol_time: int):

    try:
        int(protocol_time)
    except ValueError:
        await context.send("Your protocol time must be an integer (whole number) between 1 and 120 minutes.")

    if context.channel.name == ORDERS_REPORTING:
        await orders_reporting.report_order(context, protocol_name, protocol_time)


@bot.command()
async def ai_status(context):
    if context.channel.name == BOT_DEV_COMMS:
        await status.report_status(context, message_listeners)


@bot.command()
async def release(context, drone):
    if has_role(context.author, HIVE_MXTRESS):
        storage.release(context, drone)


@bot.event
async def on_message(message: discord.Message):

    # Ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        return

    LOGGER.info("Beginning message listener stack execution.")
    for listener in message_listeners:
        LOGGER.info(f"Executing: {listener}")
        if await listener(message):  # Return early if any listeners return true.
            return
    LOGGER.info("End of message listener stack.")

    LOGGER.info("Processing additional commands.")
    await bot.process_commands(message)


@bot.event
async def on_member_join(member: discord.Member):
    await join.on_member_join(member)


@bot.event
async def on_member_remove(member: discord.Member):
    # remove entry from DB if member was drone
    if has_any_role(member, [DRONE, STORED]):
        drone_id = get_id(member.display_name)
        drone_management.remove_drone_from_db(drone_id)


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
