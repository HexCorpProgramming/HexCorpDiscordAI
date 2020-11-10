import random
import asyncio
import logging

from discord.ext.commands import Bot
from discord import Game

# as of November 2020 only Games are supported as status for bots: https://github.com/Rapptz/discord.py/issues/2400
ACTIVITIES = [
    Game("in the conversion chamber"),
    Game("with your mind")
]

LOGGER = logging.getLogger('ai')

# status is changed every two days for now
STATUS_CHANGE_INTERVAL = 172800


async def start_change_status(bot: Bot):
    LOGGER.info("Beginning routine change of status message.")
    while True:
        # Check active orders every minute.
        LOGGER.debug("Changing status")
        await change_status(bot)
        await asyncio.sleep(STATUS_CHANGE_INTERVAL)


async def change_status(bot: Bot):
    await bot.change_presence(activity=random.choice(ACTIVITIES))
