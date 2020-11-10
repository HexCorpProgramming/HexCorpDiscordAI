import discord
import logging
from bot_utils import get_id
from db.drone_dao import is_optimized, is_glitched, is_prepending_id

LOGGER = logging.getLogger("ai")


async def update_display_name(user: discord.Member):
    drone_id = get_id(user.display_name)
    LOGGER.info(f"Optimized: {is_optimized(user)} Glitched: {is_glitched(user)} Prepending: {is_prepending_id(user)}")
    new_display_name = f"{'⬢' if is_optimized(user) or is_glitched(user) or is_prepending_id(user) else '⬡'}-Drone #{drone_id}"
    LOGGER.info("Updating drone display name.")
    LOGGER.info(f"Old name: {user.display_name}")
    LOGGER.info(f"New name: {new_display_name}")
    if user.display_name == new_display_name:
        return False
    await user.edit(nick=new_display_name)
    return True
