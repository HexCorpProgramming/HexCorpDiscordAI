import discord
import logging
from src.bot_utils import get_id
from src.db.drone_dao import is_glitched, is_prepending_id, is_optimized, is_identity_enforced, is_battery_powered, is_third_person_enforced

LOGGER = logging.getLogger("ai")


async def update_display_name(user: discord.Member):
    drone_id = get_id(user.display_name)

    tests = [
        is_optimized,
        is_glitched,
        is_prepending_id,
        is_identity_enforced,
        is_battery_powered,
        is_third_person_enforced
    ]

    icon = '⬢' if any([await t(user) for t in tests]) else '⬡'
    new_display_name = f"{icon}-Drone #{drone_id}"

    if user.display_name == new_display_name:
        # Return false if no update required.
        return False

    LOGGER.info(f"Updating drone display name. Old name: {user.display_name}. New name: {new_display_name}.")
    await user.edit(nick=new_display_name)
    return True
