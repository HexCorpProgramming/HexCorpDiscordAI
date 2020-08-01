import logging
import discord
from channels import DRONE_HIVE_CHANNELS
from roles import ENFORCER_DRONE, has_role
from resources import DRONE_AVATAR, ENFORCER_AVATAR
from webhook import get_webhook_for_channel
from id_converter import convert_id_to_member

LOGGER = logging.getLogger('ai')


async def amplify_message(context, amplification_message: str, target_channel: discord.TextChannel, drones):
    LOGGER.info("Amplifying message.")

    for drone in drones:

        LOGGER.debug(f"Preparing drone {drone} for amplification.")

        amplifier_drone = convert_id_to_member(drone)
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
