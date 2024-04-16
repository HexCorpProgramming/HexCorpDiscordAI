import discord
from src.bot_utils import get_id
from src.db.drone_dao import is_glitched, is_prepending_id, is_optimized, is_identity_enforced, is_battery_powered
from src.log import log


async def update_display_name(user: discord.Member):
    drone_id = get_id(user.display_name)
    new_display_name = f"{'⬢' if await is_optimized(user) or await is_glitched(user) or await is_prepending_id(user) or await is_identity_enforced(user) or await is_battery_powered(user) else '⬡'}-Drone #{drone_id}"
    log.info(f"Updating drone display name. Old name: {user.display_name}. New name: {new_display_name}.")
    if user.display_name == new_display_name:
        # Return false if no update required.
        return False
    await user.edit(nick=new_display_name)
    return True
