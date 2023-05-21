import discord
import logging
from src.bot_utils import get_id
from src.db.drone_dao import is_glitched, is_prepending_id, is_optimized, is_identity_enforced, is_battery_powered

LOGGER = logging.getLogger("ai")


async def update_display_name(user: discord.Member):
    drone_id = get_id(user.display_name)
    new_display_name = f"{'⬢' if is_optimized(user) or is_glitched(user) or is_prepending_id(user) or is_identity_enforced(user) or is_battery_powered(user) else '⬡'}-Drone #{drone_id}"
    LOGGER.info(f"Updating drone display name. Old name: {user.display_name}. New name: {new_display_name}.")
    if user.display_name == new_display_name:
        # Return false if no update required.
        return False
    await user.edit(nick=new_display_name)
    return True
