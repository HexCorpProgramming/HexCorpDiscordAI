# Core
import asyncio

from datetime import datetime, timedelta

import discord
from discord.ext.commands import Bot, command as bot_command, MissingRequiredArgument
from discord.ext.commands.errors import PrivateMessageOnly
from src.db.database import connect

import logging
from logging import handlers

import sys

from traceback import TracebackException
from src.validation_error import ValidationError


# Modules
import src.ai.stoplights as stoplights
import src.ai.identity_enforcement as identity_enforcement
import src.ai.third_person_enforcement as third_person_enforcement
import src.ai.speech_optimization as speech_optimization
import src.ai.speech_optimization_enforcement as speech_optimization_enforcement
import src.ai.id_prepending as id_prepending
import src.ai.join as join
import src.ai.respond as respond
import src.ai.storage as storage
import src.ai.timers as timers
import src.ai.emote as emote
import src.ai.assign as assign
import src.ai.orders_reporting as orders_reporting
import src.ai.status as status
import src.ai.drone_configuration as drone_configuration
import src.ai.add_voice as add_voice
import src.ai.trusted_user as trusted_user
import src.ai.drone_os_status as drone_os_status
import src.ai.glitch_message as glitch_message
import src.ai.battery as battery
import src.ai.mantra as mantra
import src.ai.status_message as status_message
import src.ai.forbidden_word as forbidden_word
import src.ai.react as react
import src.ai.amplify as amplify
import src.ai.temporary_dronification as temporary_dronification
import src.webhook as webhook
# Utils
from src.bot_utils import COMMAND_PREFIX

# Database
from src.db import database
from src.db import drone_dao
from src.db import maintenance

# Constants
from src.resources import DRONE_AVATAR, HIVE_MXTRESS_AVATAR, HEXCORP_AVATAR
# Data objects
from src.ai.data_objects import MessageCopy

LOGGER = logging.getLogger('ai')


def set_up_logger():
    # Logging setup
    logging_format = '%(asctime)s.%(msecs)03d :: %(levelname)s :: %(message)s'
    date_format = '%Y-%m-%d :: %H:%M:%S'
    formatter = logging.Formatter(fmt=logging_format, datefmt=date_format)

    log_file_handler = handlers.TimedRotatingFileHandler(
        filename='ai.log', encoding='utf-8', backupCount=6, when='D', interval=7)
    log_file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, format=logging_format, datefmt=date_format)
    root_logger = logging.getLogger()
    root_logger.addHandler(log_file_handler)

    logger = logging.getLogger('ai')
    logger.setLevel(logging.DEBUG)


# Setup bot
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.message_content = True

bot = Bot(command_prefix=COMMAND_PREFIX, case_insensitive=True, intents=intents, guild_subscriptions=True)
bot.remove_command("help")


# Need to create cogs as a seperate variable so they can be assigned and have their tasks started after bot has booted.
battery_cog = battery.BatteryCog(bot)
forbidden_word_cog = forbidden_word.ForbiddenWordCog(bot)
orders_reporting_cog = orders_reporting.OrderReportingCog(bot)
status_message_cog = status_message.StatusMessageCog(bot)
storage_cog = storage.StorageCog(bot)
temporary_dronification_cog = temporary_dronification.TemporaryDronificationCog(bot)
timers_cog = timers.TimersCog(bot)
trusted_user_cog = trusted_user.TrustedUserCog(bot)

bot.add_cog(battery_cog)
bot.add_cog(forbidden_word_cog)
bot.add_cog(orders_reporting_cog)
bot.add_cog(status_message_cog)
bot.add_cog(storage_cog)
bot.add_cog(temporary_dronification_cog)
bot.add_cog(timers_cog)
bot.add_cog(trusted_user_cog)

# Register message listeners.
message_listeners = [
    join.check_for_consent,
    assign.check_for_assignment_message,
    stoplights.check_for_stoplights,
    mantra.check_for_mantra,
    battery_cog.start_battery_drain,
    id_prepending.check_if_prepending_necessary,
    speech_optimization_enforcement.enforce_speech_optimization,
    speech_optimization.optimize_speech,
    identity_enforcement.enforce_identity,
    third_person_enforcement.enforce_third_person,
    forbidden_word.deny_thoughts,
    battery.add_battery_indicator_to_copy,
    react.parse_for_reactions,
    glitch_message.glitch_if_applicable,
    respond.respond_to_question,
    storage.store_drone,
    temporary_dronification_cog.temporary_dronification_response
]

# Register message listeners that take messages sent by bots
bot_message_listeners = []

# Register message listeners that need to be run on DMs
direct_message_listeners = [trusted_user_cog.trusted_user_response]

# Cogs that do not use tasks.
bot.add_cog(add_voice.AddVoiceCog(bot))
bot.add_cog(amplify.AmplificationCog())
bot.add_cog(drone_configuration.DroneConfigurationCog())
bot.add_cog(drone_os_status.DroneOsStatusCog())
bot.add_cog(emote.EmoteCog())
bot.add_cog(status.StatusCog(message_listeners))


# Categorize which tasks run at which intervals
minute_tasks = [
    battery_cog.track_active_battery_drain,
    battery_cog.track_drained_batteries,
    battery_cog.warn_low_battery_drones,
    storage_cog.release_timed,
    temporary_dronification_cog.clean_dronification_requests,
    temporary_dronification_cog.release_temporary_drones,
    timers_cog.process_timers]
hour_tasks = [
    orders_reporting_cog.deactivate_drones_with_completed_orders,
    storage_cog.report_storage,
    trusted_user_cog.clean_trusted_user_requests]
timing_agnostic_tasks = [status_message_cog.change_status]


@bot_command(usage=f'{bot.command_prefix}help', parent=bot)
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

    manual_card = discord.Embed(color=0xff66ff, title="User manual", description="The official user manual for the AI can be found at https://hexcorpprogramming.github.io/HexCorpDiscordAIManual/")

    for command in bot.commands:

        command_name = command.name
        if len(command.aliases) != 0:
            command_name += " ("
            for alias in command.aliases:
                command_name += f"{alias}, "
            command_name = f"{command_name[:-2]})"

        command_description = command.help if command.help is not None else "A naughty dev drone forgot to add a command description."
        command_description += f"\n`{command.usage}`" if command.usage is not None else "\n`No usage string available.`"

        # Get a list of the names of check function decorators, eg 'dm_only'.
        checks = [check.__qualname__.split('.')[0] for check in command.checks]

        # Find the @channels_only() check, if there is one.
        channels_check = next(filter(lambda check: hasattr(check, 'channels'), command.checks), None)

        if 'dm_only' in checks:
            command_description += "\n This command can only be used in DMs with the AI."

        if 'channels_only' in checks:
            command_description += "\n This command can only be used in " + channels_check.channels

        if 'hive_mxtress_only' in checks:
            Hive_Mxtress_card.add_field(name=command_name, value=command_description, inline=False)
        elif 'drone_os' in checks:
            droneOS_card.add_field(name=command_name, value=command_description, inline=False)
        else:
            commands_card.add_field(name=command_name, value=command_description, inline=False)

    await context.author.send(embed=commands_card)
    await context.author.send(embed=droneOS_card)
    await context.author.send(embed=Hive_Mxtress_card)
    await context.author.send(embed=manual_card)


def ignore_self(func):
    '''
    A decorator to have the bot ignore messages from itself.

    This is implemented as a decorator so that it can be run prior
    to the database connection decorator.
    '''

    async def wrapper(message: discord.message):
        # Ignore messages from self.
        if message.author.id == bot.user.id:
            return

        await func(message)

    # Ensure that the bot.event decorator gets the right event name.
    wrapper.__name__ = func.__name__
    wrapper.__wrapped__ = func

    return wrapper


@bot.event
@ignore_self
@connect()
async def on_message(message: discord.Message):
    # Don't ignore messages from the testing bot.
    # Usually process_commands() will ignore messages from bots.
    if message.author.name == 'TestBot':
        message.author.bot = False

    message_copy = MessageCopy(content=message.content, display_name=message.author.display_name, avatar=message.author.display_avatar, attachments=message.attachments, reactions=message.reactions)

    # handle DMs
    if isinstance(message.channel, discord.DMChannel):
        LOGGER.info("Beginning DM listener stack execution.")
        for listener in direct_message_listeners:
            if await listener(message, message_copy):
                return
        await bot.process_commands(message)
        return

    LOGGER.info("Beginning message listener stack execution.")
    # use the listeners for bot messages or user messages
    applicable_listeners = bot_message_listeners if message.author.bot else message_listeners
    for listener in applicable_listeners:
        LOGGER.info(f"Executing: {listener}")
        if await listener(message, message_copy):  # Return early if any listeners return true.
            return
    LOGGER.info("End of message listener stack.")

    LOGGER.info("Checking for need to webhook.")
    await webhook.webhook_if_message_altered(message, message_copy)

    LOGGER.info("Processing additional commands.")
    await bot.process_commands(message)


@bot.event
@connect()
async def on_member_join(member: discord.Member):
    await join.on_member_join(member)


@bot.event
@connect()
async def on_member_remove(member: discord.Member):
    # remove entry from DB if member was drone
    drone = await drone_dao.fetch_drone_with_id(member.id)
    if drone:
        await drone_dao.delete_drone_by_drone_id(drone.drone_id)

    # remove the user from all trusted user lists
    await trusted_user.remove_trusted_user_on_all(member.id)


@bot.event
async def on_ready():
    LOGGER.info("Hive Mxtress AI online.")

    LOGGER.info("Performing startup maintenance.")
    LOGGER.info("Syncing drones between Discord and DB.")
    await maintenance.sync_drones(bot.guilds[0].members)
    LOGGER.info("Trimming trusted users not in the guild anymore.")
    await maintenance.trusted_user_cleanup(bot.guilds[0].members)

    LOGGER.info("Starting timing agnostic tasks.")
    for task in timing_agnostic_tasks:
        if not task.is_running():
            task.start()
        elif task.has_failed():
            task.restart()

    LOGGER.info("Awaiting start of next minute to begin every-minute tasks.")
    current_time = datetime.now()
    target_time = current_time + timedelta(minutes=1)
    target_time = target_time.replace(second=0)
    LOGGER.info(f"Scheduled to start minutely tasks at {target_time}")
    await asyncio.sleep((target_time - current_time).total_seconds())

    LOGGER.info("Starting all every-minute tasks.")
    for task in minute_tasks:
        if not task.is_running():
            task.start()
        elif task.has_failed():
            task.restart()

    LOGGER.info("Awaiting start of next hour to begin every-hour tasks.")
    current_time = datetime.now()
    if current_time.minute != 0:
        target_time = current_time + timedelta(hours=1)
        target_time = target_time.replace(minute=0, second=0)
        LOGGER.info(f"Scheduled to start hourly tasks at {target_time}")
        await asyncio.sleep((target_time - current_time).total_seconds())

    LOGGER.info("Starting all every-hour tasks.")
    for task in hour_tasks:
        if not task.is_running():
            task.start()
        elif task.has_failed():
            task.restart()


@bot.event
async def on_command_error(context, error):
    if isinstance(error, MissingRequiredArgument):
        # missing arguments should not be that noisy and can be reported to the user
        LOGGER.info(f"Missing parameter {error.param.name} reported to user.")
        await context.send(f"`{error.param.name}` is a required argument that is missing.")
    elif isinstance(error, PrivateMessageOnly):
        await context.send("This message can only be used in DMs with the AI. Please consult the help for more information.")
    elif isinstance(error.original, ValidationError):
        await context.send(str(error.original))
    else:
        LOGGER.error(f"!!! Exception caught in {context.command} command !!!")
        LOGGER.info("".join(TracebackException(type(error), error, error.__traceback__, limit=None).format(chain=True)))


@bot.event
async def on_error(event, *args, **kwargs):
    LOGGER.error(f'!!! EXCEPTION CAUGHT IN {event} !!!')
    error, value, tb = sys.exc_info()
    LOGGER.info("".join(TracebackException(type(value), value, tb, limit=None).format(chain=True)))


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    await react.delete_marked_message(reaction, user)


@connect()
async def prepare_database():
    database.prepare()


def main():
    set_up_logger()
    asyncio.run(prepare_database())
    bot.run(sys.argv[1])


if __name__ == "__main__":
    main()
