from datetime import datetime, timedelta
from typing import List

import discord
from discord.ext.commands import Cog, command, UserInputError
from discord.ext import tasks
from src.bot_utils import COMMAND_PREFIX, dm_only
from src.resources import BRIEF_DRONE_OS
from src.log import log
from src.drone_member import DroneMember
from src.roles import has_role, HIVE_MXTRESS

REQUEST_TIMEOUT = timedelta(hours=24)


class TrustedUserRequest:

    def __init__(self, target: DroneMember, issuer: DroneMember, question_message_id: int):
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
    @command(usage=f"{COMMAND_PREFIX}add_trusted_user \"A trusted user\"", brief=[BRIEF_DRONE_OS])
    async def add_trusted_user(self, context, trusted_user: DroneMember):
        '''
        Add user with the given nickname as a trusted user.
        Requires trusted user to consent within 24 hours before addition.
        Use quotation marks if the username contains spaces.
        This command is used in DMs with the AI.
        '''

        if trusted_user.id == context.author.id:
            raise UserInputError("Can not add yourself to your list of trusted users.")

        author = await DroneMember.create(context.author)

        if author.drone is None:
            raise UserInputError('Only drones can add trusted members')

        if trusted_user.id in author.drone.trusted_users:
            raise UserInputError(f"User with name \"{trusted_user.display_name}\" is already trusted.")

        # request permission from trusted user and notify drone
        drone_name = context.bot.guilds[0].get_member(context.author.id).display_name
        question_message = await trusted_user.send(f"\"{drone_name}\" is requesting to add you as a trusted user. This request will expire in 24 hours. To accept or reject this request, reply to this message. (y/n)")
        question_message_id = int(question_message.id)
        request = TrustedUserRequest(trusted_user, author, question_message_id)
        log.info(f"Adding a new trusted user addition request: {request}")
        self.trusted_user_requests.append(request)
        await context.reply(f"Request sent to \"{trusted_user.display_name}\". They have 24 hours to accept.")

    @dm_only()
    @command(usage=f"{COMMAND_PREFIX}remove_trusted_user \"The untrusted user\"", brief=[BRIEF_DRONE_OS])
    async def remove_trusted_user(self, context, trusted_user: DroneMember):
        '''
        Remove a given user from the list of trusted users.
        '''

        if has_role(trusted_user, HIVE_MXTRESS):
            raise UserInputError("Can not remove the Hive Mxtress as a trusted user.")

        author = await DroneMember.create(context.author)

        if author.drone is None:
            raise UserInputError('Only drones can add trusted members')

        if trusted_user.id not in author.drone.trusted_users:
            raise UserInputError(f"User with name \"{trusted_user.display_name}\" was not trusted.")

        author.drone.trusted_users.remove(trusted_user.id)
        await author.drone.save()
        await context.reply(f"Successfully removed trusted user \"{trusted_user.display_name}\".")

    @dm_only()
    async def trusted_user_response(self, message: discord.Message, message_copy=None):
        matching_request = None
        for request in self.trusted_user_requests:
            if request.target.id == message.author.id:
                matching_request = request
                break

        if matching_request and message.reference and message.reference.message_id and message.reference.resolved.id == matching_request.question_message_id:
            log.info(f"Message detected as response to a trusted user addition request {matching_request}")

            # fetch display names of parties involved
            drone_name = request.issuer.display_name
            trusted_user_name = request.target.display_name

            # if accepted, start addition and notification process
            if message.content.lower() == "y".lower():
                log.info("Consent given for trusted user addition. Writing to DB...")

                # get trusted user list and append new trusted user
                request.issuer.drone.trusted_users.append(request.target.id)
                await request.issuer.drone.save()

                # notify user and drone of successful addition
                await message.reply(f"Consent noted. You have been added as a trusted user of \"{drone_name}\".")
                await request.issuer.send(f"\"{trusted_user_name}\" has accepted your request and is now a trusted user.")

                # remove request
                self.trusted_user_requests.remove(matching_request)

            # if rejected, discard request and notify parties involved
            elif message.content.lower() == "n".lower():
                log.info("Consent not given for trusted user addition. Removing the request.")

                # notify user and drone of rejection
                await message.reply(f"Consent not given. You have not been added as a trusted user of \"{drone_name}\".")
                await request.issuer.send(f"\"{trusted_user_name}\" has rejected your request. No changes have been made.")

                # discard request
                self.trusted_user_requests.remove(matching_request)
