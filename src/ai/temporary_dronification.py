from datetime import datetime, timedelta, timezone
from typing import List

import discord
from discord.ext.commands import Cog, command, guild_only, UserInputError
from discord.ext import tasks

from src.bot_utils import COMMAND_PREFIX
from src.db.database import connect
from src.db.drone_dao import fetch_all_elapsed_temporary_dronification
from src.ai.assign import create_drone
from src.ai.drone_configuration import unassign_drone
from src.roles import HIVE_MXTRESS, has_role
from src.log import log
from src.drone_member import DroneMember

REQUEST_TIMEOUT = timedelta(minutes=5)


class DronificationRequest:

    def __init__(self, target: discord.Member, issuer: discord.Member, hours: int, question_message: discord.Message):
        self.target = target
        self.issuer = issuer
        self.hours = hours
        self.question_message = question_message
        self.issued = datetime.now()


class TemporaryDronificationCog(Cog):

    dronification_requests: List[DronificationRequest] = []

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=1)
    @connect()
    async def clean_dronification_requests(self):
        now = datetime.now()
        self.dronification_requests = list(filter(lambda request: request.issued + REQUEST_TIMEOUT > now, self.dronification_requests))

    @tasks.loop(minutes=1)
    @connect()
    async def release_temporary_drones(self):
        log.info("Looking for temporary drones to release.")
        guild = self.bot.guilds[0]
        for drone in await fetch_all_elapsed_temporary_dronification():
            await unassign_drone(guild.get_member(drone.discord_id))

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}temporarily_dronify @AssociateName 6')
    async def temporarily_dronify(self, context, target: DroneMember, hours: int):
        '''
        Temporarily dronifies an associate for a certain amount of time.
        Associate must have been on the server for more than 24 hours.
        Requires confirmation from the associate to proceed.
        '''
        if hours <= 0:
            raise UserInputError("Hours must be greater than 0.")

        # exclude drones
        if target.drone:
            raise UserInputError(f"{target.display_name} is already a drone.")

        # exclude the Hive Mxtress
        if has_role(target, HIVE_MXTRESS):
            raise UserInputError("The Hive Mxtress is not a valid target for temporary dronification.")

        # target has to have been on the server for more than 24 hours
        if target.joined_at > (datetime.now(timezone.utc) - timedelta(hours=24)):
            raise UserInputError("Target has not been on the server for more than 24 hours. Can not temporarily dronify.")

        question_message = await context.reply(f"Target identified and locked on. Commencing temporary dronification procedure. {target.mention} you have 5 minutes to comply by replying to this message. Do you consent? (y/n)")
        request = DronificationRequest(target, context.author, hours, question_message)
        log.info(f"Adding a new request for temporary dronification: {request}")
        self.dronification_requests.append(request)

    async def temporary_dronification_response(self, message: discord.Message, message_copy=None):
        matching_request = None
        for request in self.dronification_requests:
            if request.target == message.author:
                matching_request = request
                break

        if matching_request and message.reference and message.reference.resolved == matching_request.question_message:
            log.info(f"Message detected as response to a temporary dronification request {matching_request}")
            if message.content.lower() == "y".lower():
                log.info("Consent given for temporary dronification. Changing roles and writing to DB...")
                self.dronification_requests.remove(matching_request)
                dronification_until = datetime.now() + timedelta(hours=matching_request.hours)
                plural = "hour" if int(matching_request.hours) == 1 else "hours"
                await message.reply(f"Consent noted. HexCorp dronification suite engaged for the next {matching_request.hours} {plural}.")
                await create_drone(message.guild, message.author, message.channel, [str(matching_request.issuer.id)], dronification_until)
            elif message.content.lower() == "n".lower():
                log.info("Consent not given for temporary dronification. Removing the request.")
                self.dronification_requests.remove(matching_request)
                await message.reply("Consent not given. Procedure aborted.")

        return False
