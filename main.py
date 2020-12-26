# Core
import discord
from discord.utils import get
import sys
import asyncio
import logging
import random
from typing import Union
from logging import handlers
from discord.ext.commands import Bot, MissingRequiredArgument, guild_only, dm_only, Greedy
from traceback import TracebackException

from ai.commands import DroneMemberConverter

# Modules
import ai.stoplights as stoplights
import ai.identity_enforcement as identity_enforcement
import ai.speech_optimization as speech_optimization
import ai.id_prepending as id_prepending
import ai.join as join
import ai.respond as respond
import ai.storage as storage
import ai.emote as emote
import ai.assign as assign
import ai.orders_reporting as orders_reporting
import ai.status as status
import ai.drone_management as drone_management
import ai.add_voice as add_voice
import ai.trusted_user as trusted_user
import ai.drone_os_status as drone_os_status
import ai.status_message as status_messages
import ai.glitch_message as glitch_message
from ai.mantras import Mantra_Handler
import ai.thought_denial as thought_denial
import webhook
# Utils
from bot_utils import COMMAND_PREFIX
import id_converter
# Database
from db import database
from db import drone_dao
# Constants
from roles import has_role, has_any_role, SPEECH_OPTIMIZATION, GLITCHED, ID_PREPENDING, HIVE_MXTRESS, IDENTITY_ENFORCEMENT, MODERATION_ROLES
from channels import DRONE_HIVE_CHANNELS, OFFICE, ORDERS_REPORTING, REPETITIONS, BOT_DEV_COMMS
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

    return logger


# Setup bot
intents = discord.Intents.default()
intents.members = True

bot = Bot(command_prefix=COMMAND_PREFIX, case_insensitive=True, intents=intents)
bot.remove_command("help")

# Instance modules
mantra_handler = Mantra_Handler(bot)

# Run-forever checkers.
checking_for_completed_orders = False
reporting_storage = False
checking_for_stored_drones_to_release = False
updating_status_message = False

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
    member_drones = id_converter.convert_ids_to_members(context.guild, drones) | set(context.message.mentions)

    if not has_role(context.author, HIVE_MXTRESS) and context.channel.name == OFFICE:
        return

    channel_webhook = await webhook.get_webhook_for_channel(target_channel)

    for drone in member_drones:
        LOGGER.info("Amplifying message!!")
        await webhook.proxy_message_by_webhook(message_content=message,
                                               message_username=drone.display_name,
                                               message_avatar=drone.avatar_url if not identity_enforcement.identity_enforcable(drone, channel=target_channel) else DRONE_AVATAR,
                                               webhook=channel_webhook)


@guild_only()
@bot.command(aliases=['tid'], brief="DroneOS", usage=f'{bot.command_prefix}toggle_id_prepending 5890 9813')
async def toggle_id_prepending(context, drones: Greedy[Union[discord.Member, DroneMemberConverter]]):
    '''
    Allows the Hive Mxtress or trusted users to enforce mandatory ID prepending upon specified drones.
    '''
    await drone_management.toggle_parameter(context,
                                            drones,
                                            "id_prepending",
                                            get(context.guild.roles, name=ID_PREPENDING),
                                            drone_dao.is_prepending_id,
                                            lambda: "ID prepending is now mandatory.",
                                            lambda: "Prepending? More like POST pending now that that's over! Haha!" if random.randint(1, 100) == 66 else "ID prependment policy relaxed.")


@guild_only()
@bot.command(aliases=['optimize', 'toggle_speech_op', 'tso'], brief="DroneOS", usage=f'{bot.command_prefix}toggle_speech_optimization 5890 9813')
async def toggle_speech_optimization(context, drones: Greedy[Union[discord.Member, DroneMemberConverter]]):
    '''
    Lets the Hive Mxtress or trusted users toggle drone speech optimization.
    '''
    await drone_management.toggle_parameter(context,
                                            drones,
                                            "optimized",
                                            get(context.guild.roles, name=SPEECH_OPTIMIZATION),
                                            drone_dao.is_optimized,
                                            lambda: "Speech optimization is now active.",
                                            lambda: "Speech optimization disengaged.")


@guild_only()
@bot.command(aliases=['tei'], brief="DroneOS", usage=f'{bot.command_prefix}toggle_enforce_identity 5890 9813')
async def toggle_enforce_identity(context, drones: Greedy[Union[discord.Member, DroneMemberConverter]]):
    '''
    Lets the Hive Mxtress or trusted users toggle drone identity enforcement.
    '''
    await drone_management.toggle_parameter(context,
                                            drones,
                                            "identity_enforcement",
                                            get(context.guild.roles, name=IDENTITY_ENFORCEMENT),
                                            drone_dao.is_identity_enforced,
                                            lambda: "Identity enforcement is now active.",
                                            lambda: "Identity enforcement disengaged.")


@guild_only()
@bot.command(aliases=['glitch', 'tdg'], brief="DroneOS", usage=f'{bot.command_prefix}toggle_drone_glitch 9813 3287')
async def toggle_drone_glitch(context, drones: Greedy[Union[discord.Member, DroneMemberConverter]]):
    '''
    Lets the Hive Mxtress or trusted users toggle drone glitch levels.
    '''
    await drone_management.toggle_parameter(context,
                                            drones,
                                            "glitched",
                                            get(context.guild.roles, name=GLITCHED),
                                            drone_dao.is_glitched,
                                            lambda: "Uh.. it’s probably not a problem.. probably.. but I’m showing a small discrepancy in... well, no, it’s well within acceptable bounds again. Sustaining sequence." if random.randint(1, 100) == 66 else "Drone corruption at un̘͟s̴a̯f̺e͈͡ levels.",
                                            lambda: "Drone corruption at acceptable levels.")


@guild_only()
@bot.command(brief="DroneOS", usage=f'{bot.command_prefix}emergency_release 9813')
async def emergency_release(context, drone_id: str):
    '''
    Lets moderators disable all DroneOS restrictions currently active on a drone.
    '''
    if has_any_role(context.author, MODERATION_ROLES):
        await drone_management.emergency_release(context, drone_id)


@dm_only()
@bot.command(usage=f"{bot.command_prefix}unassign", brief="DroneOS")
async def unassign(context):
    '''
    Allows a drone to go back to the status of an Associate.
    '''
    await drone_management.unassign_drone(context)


@guild_only()
@bot.command(usage=f'{bot.command_prefix}rename 1234 3412', brief="Hive Mxtress")
async def rename(context, old_id, new_id):
    '''
    Allows the Hive Mxtress to change the ID of a drone.
    '''
    if context.channel.name == OFFICE and has_role(context.author, HIVE_MXTRESS):
        await drone_management.rename_drone(context, old_id, new_id)


@dm_only()
@bot.command(usage=f'{bot.command_prefix}drone_status 9813', brief="DroneOS")
async def drone_status(context, drone_id: str):
    '''
    Displays all the DroneOS information you have access to about a drone.
    '''
    response = drone_os_status.get_status(drone_id, context.author.id)
    if response is None:
        await context.send(f"No drone with ID {drone_id} found.")
    if response is not None:
        await context.send(embed=response)


@dm_only()
@bot.command(usage=f"{bot.command_prefix}add_trusted_user \"A trusted user\"", brief="DroneOS")
async def add_trusted_user(context, user_name: str):
    '''
    Add user with the given nickname as a trusted user.
    Use quotation marks if the username contains spaces.
    This command is used in DMs with the AI.
    '''
    await trusted_user.add_trusted_user(context, user_name)


@dm_only()
@bot.command(usage=f"{bot.command_prefix}remove_trusted_user \"The untrusted user\"", brief="DroneOS")
async def remove_trusted_user(context, user_name: str):
    '''
    Remove a given user from the list of trusted users.
    Use quotation marks if the username contains spaces.
    This command is used in DMs with the AI.
    '''
    await trusted_user.remove_trusted_user(context, user_name)


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
@bot.command(usage=f'{bot.command_prefix}release 9813', brief="Hive Mxtress")
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

    message_copy = MessageCopy(message.content, message.author.display_name, message.author.avatar_url)

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
        drone_management.remove_drone_from_db(drone.drone_id)


@bot.event
async def on_ready():
    drone_dao.add_new_drone_members(bot.guilds[0].members)
    await mantra_handler.load_mantra()
    global checking_for_completed_orders, reporting_storage, checking_for_stored_drones_to_release, updating_status_message

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

if __name__ == "__main__":
    LOGGER = set_up_logger()

    # Prepare database
    database.prepare()

    bot.run(sys.argv[1])
