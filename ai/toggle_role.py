import discord
from discord.utils import get
from roles import has_role
from typing import List
import logging
from webhook import get_webhook_for_channel
from bot_utils import get_id

LOGGER = logging.getLogger("ai")


async def toggle_role(context, targets: List[discord.Member], role_name: str, toggle_on: str, toggle_off: str):

    if (role := get(context.guild.roles, name=role_name)) is None:
        return

    webhook = await get_webhook_for_channel(context.channel)

    for target in targets:

        target_drone_id = get_id(target.display_name)

        if has_role(target, role_name):
            LOGGER.info(f"Removing {role_name} from {target.display_name}")
            await target.remove_roles(role)
            await webhook.send(f"{target_drone_id} :: {toggle_off}", username=target.display_name, avatar_url=target.avatar_url)
        else:
            LOGGER.info(f"Adding {role_name} to {target.display_name}")
            await target.add_roles(role)
            await webhook.send(f"{target_drone_id} :: {toggle_on}", username=target.display_name, avatar_url=target.avatar_url)

    LOGGER.info("All roles updated for all targets.")
