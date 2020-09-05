# Core
import discord
import sys
import asyncio
import logging
from logging import handlers
from discord.ext.commands import Bot, MissingRequiredArgument, guild_only, dm_only
from traceback import TracebackException

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
import ai.add_voice as add_voice
from ai.mantras import Mantra_Handler
import webhook
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
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d :: %(levelname)s :: %(message)s', datefmt='%Y-%m-%d :: %H:%M:%S')

log_file_handler = handlers.TimedRotatingFileHandler(
    filename='ai.log', encoding='utf-8', backupCount=6, when='D', interval=7)
log_file_handler.setFormatter(formatter)

logging.basicConfig(level=logging.WARNING)
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


@guild_only()
@bot.command(usage=f'{bot.command_prefix}emote "beep boop"', aliases=['big', 'emote'])
async def bigtext(context, sentence):
    '''
    Let the AI say things using emotes.
    '''
    if context.channel.name not in DRONE_HIVE_CHANNELS:
        if (reply := emote.generate_big_text(context.channel, sentence)):
            await context.send(reply)


@guild_only()
@bot.command(brief="Hive Mxtress", usage=f'{bot.command_prefix}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287')
async def amplify(context, message: str, target_channel: discord.TextChannel, *drones):
    '''
    Allows the Hive Mxtress to speak through other drones.
    '''
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        target_webhook = await webhook.get_webhook_for_channel(target_channel)
        for amp_profile in amplifier.generate_amplification_information(target_channel, drones):
            if amp_profile is not None:
                await target_webhook.send(message, username=amp_profile["username"], avatar_url=amp_profile["avatar_url"])


@guild_only()
@bot.command(aliases=['optimize', 'toggle_speech_op', 'tso'], brief="Hive Mxtress", usage=f'{bot.command_prefix}toggle_speech_optimization 5890 9813')
async def toggle_speech_optimization(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone speech optimization.
    '''

    member_drones = id_converter.convert_ids_to_members(context.guild, drones)

    if has_role(context.author, HIVE_MXTRESS):
        await toggle_role.toggle_role(context, member_drones | set(context.message.mentions), SPEECH_OPTIMIZATION, "Speech optimization is now active.", "Speech optimization disengaged.")


@guild_only()
@bot.command(aliases=['glitch', 'tdg'], brief="Hive Mxtress", usage=f'{bot.command_prefix}toggle_drone_glitch 9813 3287')
async def toggle_drone_glitch(context, *drones):
    '''
    Lets the Hive Mxtress or trusted users toggle drone glitch levels.
    '''

    member_drones = id_converter.convert_ids_to_members(context.guild, drones)

    if has_role(context.author, HIVE_MXTRESS):
        await toggle_role.toggle_role(context, member_drones | set(context.message.mentions), GLITCHED, "Drone corruption at un̘͟s̴a̯f̺e͈͡ levels.", "Drone corruption at acceptable levels.")


@guild_only()
@bot.command(usage=f"{bot.command_prefix}unassign 1234")
async def unassign(context, drone):
    '''
    Allows the Hive Mxtress to return a drone back to the status of an Associate.
    '''
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await drone_management.unassign_drone(context, drone)


@guild_only()
@bot.command(usage=f'{bot.command_prefix}rename 1234 3412')
async def rename(context, old_id, new_id):
    '''
    Allows the Hive Mxtress to change the ID of a drone.
    '''
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await drone_management.rename_drone(context, old_id, new_id)


@bot.command(usage=f'{bot.command_prefix}help')
async def help(context):
    '''
    Displays this help.
    '''
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
    # TODO: hidden until DroneOS is officially released
    # await context.send(embed=droneOS_card)
    await context.send(embed=Hive_Mxtress_card)


@guild_only()
@bot.command(brief="Hive Mxtress", usage=f'{bot.command_prefix}repeat "Obey HexCorp."')
async def repeat(context, *messages):
    '''
    Allows the Hive Mxtress to set a new mantra for drones to repeat.
    '''
    if context.channel.name == REPETITIONS and has_role(context.author, HIVE_MXTRESS):
        await mantra_handler.update_mantra(context.message, messages)


@guild_only()
@bot.command(aliases=["report_order"], usage=f'{bot.command_prefix}report maid 35')
async def report(context, protocol_name: str, protocol_time: int):
    '''
    Report your orders in the appropriate channel to serve the Hive. The duration can be a maximum of 120 minutes.
    '''
    try:
        int(protocol_time)
    except ValueError:
        await context.send("Your protocol time must be an integer (whole number) between 1 and 120 minutes.")

    if context.channel.name == ORDERS_REPORTING:
        await orders_reporting.report_order(context, protocol_name, protocol_time)


@guild_only()
@bot.command(usage=f'{bot.command_prefix}ai_status')
async def ai_status(context):
    '''
    A debug command, that displays information about the AI.
    '''
    if context.channel.name == BOT_DEV_COMMS:
        await status.report_status(context, message_listeners)


@guild_only()
@bot.command(usage=f'{bot.command_prefix}release 9813')
async def release(context, drone):
    '''
    Allows the Hive Mxtress to release a drone from storage.
    '''
    if has_role(context.author, HIVE_MXTRESS):
        await storage.release(context, drone)


@dm_only()
@bot.command(usage=f'{bot.command_prefix}request_voice_role')
async def request_voice_role(context):
    '''
    Gives you the Voice role and thus access to voice channels if you have been on the server for more than 2 weeks.
    '''
    await add_voice.add_voice(context, bot.guilds[0])


@bot.event
async def on_message(message: discord.Message):
    # Ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        return

    # handle DMs
    if isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
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
        asyncio.ensure_future(orders_reporting.start_check_for_completed_orders(bot))

    if not reporting_storage:
        asyncio.ensure_future(storage.start_report_storage(bot))

    if not checking_for_stored_drones_to_release:
        asyncio.ensure_future(storage.start_release_timed(bot))


@bot.event
async def on_command_error(context, error):
    if isinstance(error, MissingRequiredArgument):
        # missing arguments should not be that noisy and can be reported to the user
        LOGGER.info(f"Missing parameter {error.param.name} reported to user.")
        await context.send(f"`{error.param.name}` is a required argument that is missing.")
    else:
        LOGGER.error(f"!!! Exception caught in {context.command} command !!!")
        LOGGER.info("".join(TracebackException(type(error), error, error.__traceback__, limit=None).format(chain=True)))


@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(f'!!! EXCEPTION CAUGHT IN {event} !!!')
    error, value, tb = sys.exc_info()
    LOGGER.info("".join(TracebackException(type(value), value, tb, limit=None).format(chain=True)))

bot.run(sys.argv[1])
