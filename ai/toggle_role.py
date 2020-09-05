import discord
from discord.utils import get
from roles import has_role
from typing import List
import logging
from webhook import get_webhook_for_channel
from bot_utils import get_id

LOGGER = logging.getLogger("ai")


async def toggle_role_of_many(context, targets: List[discord.Member], role_name: str, toggle_on_message: str, toggle_off_message: str):

    for target in targets:
        toggle_role_of_one(context, target, role_name, toggle_on_message, toggle_off_message)
    LOGGER.info("All roles updated for all targets.")


async def toggle_role_of_one(context, target, role_name, toggle_on_message, toggle_off_message):

    if (role := get(context.guild.roles, name=role_name)) is None:
        return

    target_drone_id = get_id(target.display_name)
    webhook = await get_webhook_for_channel(context.channel)

    if has_role(target, role_name):
        LOGGER.info(f"Removing {role_name} from {target.display_name}")
        await target.remove_roles(role)
        await webhook.send(f"{target_drone_id} :: {toggle_off_message}", username=target.display_name, avatar_url=target.avatar_url)
        return False
    else:
        LOGGER.info(f"Adding {role_name} to {target.display_name}")
        await target.add_roles(role)
        await webhook.send(f"{target_drone_id} :: {toggle_on_message}", username=target.display_name, avatar_url=target.avatar_url)
        return True
