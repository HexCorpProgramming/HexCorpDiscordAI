import discord
from discord.utils import get
from roles import has_role
from typing import List
import logging
from webhook import get_webhook_for_channel
from bot_utils import get_id

LOGGER = logging.getLogger("ai")


async def toggle_role(context, targets: List[discord.Member], role_name: str, role_name_natural: str = None):

    if (role := get(context.guild.roles, name=role_name)) is None:
        return

    if role_name_natural is None:
        role_name_natural = role_name

    webhook = await get_webhook_for_channel(context.channel)

    for target in targets:

        target_drone_id = get_id(target.display_name)

        if has_role(target, role_name):
            LOGGER.info(f"Removing {role_name} from {target.display_name}")
            await target.remove_roles(role)
            await webhook.send(f"{target_drone_id} :: {role_name_natural} is now inactive.", username=target.display_name, avatar_url=target.avatar_url)
        else:
            LOGGER.info(f"Adding {role_name} to {target.display_name}")
            await target.add_roles(role)
            await webhook.send(f"{target_drone_id} :: {role_name_natural} is now active.", username=target.display_name, avatar_url=target.avatar_url)

    LOGGER.info("All roles updated for all targets.")
