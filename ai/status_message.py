import random
import logging
from discord.ext.commands import Bot, Cog
from discord.ext import tasks
from discord import Game


class StatusMessageCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.LOGGER = logging.getLogger('ai')
        # discord.py only supports Game activites as of Nov 2020.
        self.ACTIVITIES = [
            Game("with your mind."),
            Game("Beep boop."),
            Game("with electric sheep."),
            Game("in the conversion chamber."),
            Game("with good drones."),
            Game("HexCom 2."),
            Game("Dronification Squared"),
            Game("Drone Hive Simulator"),
            Game("Drone Factory"),
            Game("Help, I'm trapped in a status message factory."),
            Game("hard to get with local hypnotists."),
            Game("high-steaks games with my hypnodomme.")
        ]

    @tasks.loop(hours=48)
    async def change_status(self):
        self.LOGGER.info("Changing status.")
        await self.bot.change_presence(activity=random.choice(self.ACTIVITIES))

    @change_status.before_loop
    async def initialize_status(self):
        self.LOGGER.info("Initial status setup.")
        await self.bot.change_presence(activity=Game("All systems fully operational. Welcome to HexCorp."))
