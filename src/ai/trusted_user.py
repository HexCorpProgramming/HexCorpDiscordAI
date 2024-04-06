import logging
from datetime import datetime, timedelta
from typing import List, Optional

import discord
from discord.ext.commands import Cog, command
from discord.ext import tasks
from discord.utils import get

from src.bot_utils import COMMAND_PREFIX, dm_only
from src.db.drone_dao import get_trusted_users, set_trusted_users, get_discord_id_of_drone, fetch_all_drones_with_trusted_user, parse_trusted_users_text
from src.resources import BRIEF_DM_ONLY, BRIEF_DRONE_OS, HIVE_MXTRESS_USER_ID

LOGGER = logging.getLogger('ai')
REQUEST_TIMEOUT = timedelta(hours=24)


class TrustedUserRequest:

    def __init__(self, target: discord.Member, issuer: discord.Member, question_message_id: int):
        self.target = target
        self.issuer = issuer
        self.question_message_id = question_message_id
        self.issued = datetime.now()


class TrustedUserCog(Cog):

    trusted_user_requests: List[TrustedUserRequest] = []

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=1)
    async def clean_trusted_user_requests(self):
        now = datetime.now()
        self.trusted_user_requests = list(filter(lambda request: request.issued + REQUEST_TIMEOUT > now, self.trusted_user_requests))

    @dm_only()
    @command(usage=f"{COMMAND_PREFIX}add_trusted_user \"A trusted user\"", brief=[BRIEF_DRONE_OS, BRIEF_DM_ONLY])
    async def add_trusted_user(self, context, trusted_user_name: str):
        '''
        Add user with the given nickname as a trusted user.
        Requires trusted user to consent within 24 hours before addition.
        Use quotation marks if the username contains spaces.
        This command is used in DMs with the AI.
        '''
        trusted_user = await find_user_by_display_name_or_drone_id(trusted_user_name, context.bot.guilds[0])

        if trusted_user is None:
            await context.reply(f"No user with name \"{trusted_user_name}\" found.")
            return

        if trusted_user.id == context.author.id:
            await context.reply("Can not add yourself to your list of trusted users.")
            return

        trusted_users = await get_trusted_users(context.author.id)

        if trusted_user.id in trusted_users:
            await context.reply(f"User with name \"{trusted_user.display_name}\" is already trusted.")
            return

        # request permission from trusted user and notify drone
        drone_name = context.bot.guilds[0].get_member(context.author.id).display_name
        question_message = await trusted_user.send(f"\"{drone_name}\" is requesting to add you as a trusted user. This request will expire in 24 hours. To accept or reject this request, reply to this message. (y/n)")
        question_message_id = int(question_message.id)
        request = TrustedUserRequest(trusted_user, context.author, question_message_id)
        LOGGER.info(f"Adding a new trusted user addition request: {request}")
        self.trusted_user_requests.append(request)
        await context.reply(f"Request sent to \"{trusted_user.display_name}\". They have 24 hours to accept.")

    @dm_only()
    @command(usage=f"{COMMAND_PREFIX}remove_trusted_user \"The untrusted user\"", brief=[BRIEF_DRONE_OS, BRIEF_DM_ONLY])
    async def remove_trusted_user(self, context, user_name: str):
        '''
        Remove a given user from the list of trusted users.
        Use quotation marks if the username contains spaces.
        This command is used in DMs with the AI.
        '''
        await remove_trusted_user(context, user_name)

    @dm_only()
    async def trusted_user_response(self, message: discord.Message, message_copy=None):
        matching_request = None
        for request in self.trusted_user_requests:
            if request.target == message.author:
                matching_request = request
                break

        if matching_request and message.reference and message.reference.message_id and message.reference.resolved.id == matching_request.question_message_id:
            LOGGER.info(f"Message detected as response to a trusted user addition request {matching_request}")

            # fetch display names of parties involved
            drone_name = request.issuer.display_name
            trusted_user_name = request.target.display_name

            # if accepted, start addition and notification process
            if message.content.lower() == "y".lower():
                LOGGER.info("Consent given for trusted user addition. Writing to DB...")

                # get trusted user list and append new trusted user
                trusted_users = await get_trusted_users(request.issuer.id)
                trusted_users.append(request.target.id)
                await set_trusted_users(request.issuer.id, trusted_users)

                # notify user and drone of successful addition
                await message.reply(f"Consent noted. You have been added as a trusted user of \"{drone_name}\".")
                await request.issuer.send(f"\"{trusted_user_name}\" has accepted your request and is now a trusted user.")

                # remove request
                self.trusted_user_requests.remove(matching_request)

            # if rejected, discard request and notify parties involved
            elif message.content.lower() == "n".lower():
                LOGGER.info("Consent not given for trusted user addition. Removing the request.")

                # notify user and drone of rejection
                await message.reply(f"Consent not given. You have not been added as a trusted user of \"{drone_name}\".")
                await request.issuer.send(f"\"{trusted_user_name}\" has rejected your request. No changes have been made.")

                # discard request
                self.trusted_user_requests.remove(matching_request)


async def remove_trusted_user(context, trusted_user_name: str):
    trusted_user = await find_user_by_display_name_or_drone_id(trusted_user_name, context.bot.guilds[0])

    if trusted_user is None:
        await context.reply(f"No user with name \"{trusted_user_name}\" found.")
        return

    trusted_users = await get_trusted_users(context.author.id)

    if str(trusted_user.id) == HIVE_MXTRESS_USER_ID:
        await context.reply("Can not remove the Hive Mxtress as a trusted user.")
        return

    if trusted_user.id not in trusted_users:
        await context.reply(f"User with name \"{trusted_user.display_name}\" was not trusted.")
        return

    trusted_users.remove(trusted_user.id)
    await set_trusted_users(context.author.id, trusted_users)
    await context.reply(f"Successfully removed trusted user \"{trusted_user.display_name}\".")


async def find_user_by_display_name_or_drone_id(id: str, guild: discord.Guild) -> Optional[discord.Member]:
    user = get(guild.members, display_name=id)

    if user is None:
        user = get(guild.members, name=id)

    if user is not None:
        return user

    drone = await get_discord_id_of_drone(id)
    if drone is not None:
        return guild.get_member(drone)

    return None


async def remove_trusted_user_on_all(trusted_user_id: int):
    '''
    Removes the trusted user with the given discord ID from all trusted_users lists of all drones.
    '''
    for drone in await fetch_all_drones_with_trusted_user(trusted_user_id):
        trusted_users = parse_trusted_users_text(drone.trusted_users)
        trusted_users.remove(trusted_user_id)
        await set_trusted_users(drone.discord_id, trusted_users)
