import random

from discord import Game
from discord.ext import tasks
from discord.ext.commands import Bot, Cog
from src.db.database import connect
from src.log import log


class StatusMessageCog(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

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
            Game("high-stakes games with my hypnodomme.")
        ]

    @tasks.loop(hours=48)
    @connect()
    async def change_status(self):
        activity = random.choice(self.ACTIVITIES)
        log.info('Changing status to: ' + activity.name)
        await self.bot.change_presence(activity=activity)

    @change_status.before_loop
    async def initialize_status(self):
        log.info("Initial status setup.")
        await self.bot.change_presence(activity=Game("All systems fully operational. Welcome to HexCorp."))
