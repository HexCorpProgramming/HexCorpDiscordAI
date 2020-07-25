import logging
import re
import discord
from db.drone_dao import get_discord_id_of_drone
from channels import DRONE_HIVE_CHANNELS
from roles import ENFORCER_DRONE, has_role
from resources import DRONE_AVATAR, ENFORCER_AVATAR
from webhook import get_webhook_for_channel

LOGGER = logging.getLogger('ai')


async def amplify_message(context, amplification_message: str, target_channel: discord.TextChannel, drones):
    LOGGER.info("Amplifying message.")

    for drone in drones:

        LOGGER.debug(f"Preparing drone {drone} for amplification.")

        if not re.match(r"\d{4}", drone):
            continue  # Skip non-drone IDs.

        LOGGER.debug("Getting discord ID from database.")
        if (drone_from_db := get_discord_id_of_drone(drone)) is None:
            continue  # Given drone does not exist on server.

        amplifier_drone = context.guild.get_member(drone_from_db.id)
        if amplifier_drone is None:
            continue  # If getting the member somehow failed, keep calm and carry on.

        webhook = await get_webhook_for_channel(target_channel)

        amplification_avatar = amplifier_drone.avatar_url
        if target_channel.name in DRONE_HIVE_CHANNELS:
            if has_role(amplifier_drone, ENFORCER_DRONE):
                amplification_avatar = ENFORCER_AVATAR
            else:
                amplification_avatar = DRONE_AVATAR

        LOGGER.debug(f"Amplifying message with unit {drone}")
        await webhook.send(content=f"{drone} :: {amplification_message}",
                           username=amplifier_drone.display_name,
                           avatar_url=amplification_avatar)
