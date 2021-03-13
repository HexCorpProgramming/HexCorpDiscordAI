import logging
from datetime import datetime, timedelta
from typing import List

import discord
from discord.ext.commands import Cog, command, guild_only
from discord.ext import tasks

from bot_utils import COMMAND_PREFIX
from db.drone_dao import is_drone, fetch_all_elapsed_temporary_dronification
from ai.assign import create_drone
from ai.drone_configuration import unassign_drone

LOGGER = logging.getLogger('ai')
REQUEST_TIMEOUT = timedelta(minutes=5)


class DronificationRequest:

    def __init__(self, target: discord.Member, issuer: discord.Member, hours: int, question_message: discord.Message):
        self.target = target
        self.issuer = issuer
        self.hours = hours
        self.question_message = question_message
        self.issued = datetime.now()


class TemporaryDronificationCog(Cog):

    dronfication_requests: List[DronificationRequest] = []

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=1)
    async def clean_dronification_requests(self):
        now = datetime.now()
        self.dronfication_requests = filter(lambda request: request.issued + REQUEST_TIMEOUT > now, self.dronfication_requests)

    @tasks.loop(minutes=1)
    async def release_temporary_drones(self):
        LOGGER.info("Looking for temporary drones to release.")
        guild = self.bot.guilds[0]
        for drone in fetch_all_elapsed_temporary_dronification():
            unassign_drone(guild.get_member(drone.id))

    @guild_only()
    @command(usage=f'{COMMAND_PREFIX}temporarily_dronify @Associate Beep 6')
    async def temporarily_dronify(self, context, target: discord.Member, hours: int):
        if hours <= 0:
            await context.reply("Hours must be greater than 0.")
            return

        # exclude drones
        if is_drone(target):
            await context.reply(f"{target.display_name} is already a drone.")
            return

        question_message = await context.reply(f"Target identified and locked on. Commencing temporary dronification procedure. {target.mention} you have 5 minutes to comply. Do you consent? (y/n)")
        request = DronificationRequest(target, context.author, hours, question_message)
        LOGGER.info(f"Adding a new request for temporary dronification: {request}")
        self.dronfication_requests.append(request)

    async def temporary_dronification_response(self, message: discord.Message, message_copy=None):
        matching_request = None
        for request in self.dronfication_requests:
            if request.target == message.author:
                matching_request = request
                break

        if matching_request and message.reference.resolved == matching_request.question_message:
            LOGGER.info(f"Message detected as response to a temporary dronification request {matching_request}")
            if message.content.lower() == "y".lower():
                LOGGER.info("Consent given for temporary dronification. Changing roles and writing to DB...")
                self.dronfication_requests.remove(matching_request)
                dronification_until = datetime.now() + timedelta(hours=matching_request.hours)
                await message.reply(f"Consent noted. HexCorp dronification suite engaged for the next {matching_request.hours} hours.")
                await create_drone(message.guild, message.author, message.channel, [str(matching_request.issuer.id)], dronification_until)
            elif message.content.lower() == "n".lower():
                LOGGER.info("Consent not given for temporary dronification. Removing the request.")
                self.dronfication_requests.remove(matching_request)
                await message.reply("Consent not given. Procedure aborted.")

        return False
