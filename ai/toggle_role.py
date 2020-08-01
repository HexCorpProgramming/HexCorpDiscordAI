import discord
from discord.utils import get
from roles import has_role
from typing import List
import logging

LOGGER = logging.getLogger("ai")


async def toggle_role(context, targets: List[discord.Member], role_name: str):

    if (role := get(context.guild.roles, name=role_name)) is None:
        return

    for target in targets:
        if has_role(target, role_name):
            LOGGER.info(f"Removing {role_name} from {target.display_name}")
            await target.remove_roles(role)
            await context.send(f"{role_name} toggled off for {target.display_name}")
        else:
            LOGGER.info(f"Adding {role_name} to {target.display_name}")
            await target.add_roles(role)
            await context.send(f"{role_name} toggled on for {target.display_name}")

    LOGGER.info("All roles added to all targets.")
