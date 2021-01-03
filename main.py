# Core
import discord
import sys
import asyncio
import logging
from logging import handlers
from discord.ext.commands import Bot, MissingRequiredArgument
from traceback import TracebackException

# Modules
import ai.stoplights as stoplights
import ai.identity_enforcement as identity_enforcement
import ai.speech_optimization as speech_optimization
import ai.id_prepending as id_prepending
import ai.join as join
import ai.respond as respond
import ai.storage as storage
import ai.timers as timers
import ai.emote as emote
import ai.assign as assign
import ai.orders_reporting as orders_reporting
import ai.status as status
import ai.drone_configuration as drone_configuration
import ai.add_voice as add_voice
import ai.trusted_user as trusted_user
import ai.drone_os_status as drone_os_status
import ai.status_message as status_messages
import ai.glitch_message as glitch_message
from ai.mantras import Mantra_Handler
import ai.thought_denial as thought_denial
import ai.amplify as amplify
import webhook
# Utils
from bot_utils import COMMAND_PREFIX

# Database
from db import database
from db import drone_dao
# Constants
from resources import DRONE_AVATAR, HIVE_MXTRESS_AVATAR, HEXCORP_AVATAR
# Data objects
from ai.data_objects import MessageCopy

LOGGER = logging.getLogger('ai')


def set_up_logger():
    # Logging setup
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d :: %(levelname)s :: %(message)s', datefmt='%Y-%m-%d :: %H:%M:%S')

    log_file_handler = handlers.TimedRotatingFileHandler(
        filename='ai.log', encoding='utf-8', backupCount=6, when='D', interval=7)
    log_file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING)
    root_logger = logging.getLogger()
    root_logger.addHandler(log_file_handler)

    logger = logging.getLogger('ai')
    logger.setLevel(logging.DEBUG)


# Setup bot
intents = discord.Intents.default()
intents.members = True

bot = Bot(command_prefix=COMMAND_PREFIX, case_insensitive=True, intents=intents)
bot.remove_command("help")

# Run-forever checkers.
checking_for_completed_orders = False
reporting_storage = False
checking_for_stored_drones_to_release = False
updating_status_message = False
checking_for_elapsed_timers = False

# Register message listeners.
message_listeners = [
    join.check_for_consent,
    assign.check_for_assignment_message,
    stoplights.check_for_stoplights,
    id_prepending.check_if_prepending_necessary,
    speech_optimization.optimize_speech,
    identity_enforcement.enforce_identity,
    thought_denial.deny_thoughts,
    glitch_message.glitch_if_applicable,
    respond.respond_to_question,
    storage.store_drone,

]

bot.add_cog(emote.EmoteCog())
bot.add_cog(drone_configuration.DroneConfigurationCog())
bot.add_cog(add_voice.AddVoiceCog(bot))
bot.add_cog(trusted_user.TrustedUserCog())
bot.add_cog(drone_os_status.DroneOsStatusCog())
bot.add_cog(storage.StorageCog())
bot.add_cog(orders_reporting.OrderReportingCog())
bot.add_cog(status.StatusCog(message_listeners))
bot.add_cog(Mantra_Handler(bot))
bot.add_cog(amplify.AmplificationCog())


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

    await context.author.send(embed=commands_card)
    await context.author.send(embed=droneOS_card)
    await context.author.send(embed=Hive_Mxtress_card)


@bot.event
async def on_message(message: discord.Message):
    # Ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        return

    # handle DMs
    if isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
        return

    message_copy = MessageCopy(message.content, message.author.display_name, message.author.avatar_url, message.attachments)

    LOGGER.info("Beginning message listener stack execution.")
    for listener in message_listeners:
        LOGGER.info(f"Executing: {listener}")
        if await listener(message, message_copy):  # Return early if any listeners return true.
            return
    LOGGER.info("End of message listener stack.")

    LOGGER.info("Checking for need to webhook.")
    await webhook.webhook_if_message_altered(message, message_copy)

    LOGGER.info("Processing additional commands.")
    await bot.process_commands(message)


@bot.event
async def on_member_join(member: discord.Member):
    await join.on_member_join(member)


@bot.event
async def on_member_remove(member: discord.Member):
    # remove entry from DB if member was drone
    drone = drone_dao.fetch_drone_with_id(member.id)
    if drone:
        drone_configuration.remove_drone_from_db(drone.drone_id)


@bot.event
async def on_ready():
    drone_dao.add_new_drone_members(bot.guilds[0].members)
    global checking_for_completed_orders, reporting_storage, checking_for_stored_drones_to_release, updating_status_message, checking_for_elapsed_timers

    if not checking_for_completed_orders:
        asyncio.ensure_future(orders_reporting.start_check_for_completed_orders(bot))
        checking_for_completed_orders = True

    if not reporting_storage:
        asyncio.ensure_future(storage.start_report_storage(bot))
        reporting_storage = True

    if not checking_for_stored_drones_to_release:
        asyncio.ensure_future(storage.start_release_timed(bot))
        checking_for_stored_drones_to_release = True

    if not updating_status_message:
        asyncio.ensure_future(status_messages.start_change_status(bot))
        updating_status_message = True

    if not checking_for_elapsed_timers:
        asyncio.ensure_future(timers.start_process_timers(bot))
        checking_for_elapsed_timers = True


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


def main():
    set_up_logger()

    # Prepare database
    database.prepare()

    bot.run(sys.argv[1])


if __name__ == "__main__":
    main()
