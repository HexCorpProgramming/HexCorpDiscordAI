import logging
from channels import DRONE_HIVE_CHANNELS
from roles import ENFORCER_DRONE, has_role
from resources import DRONE_AVATAR, ENFORCER_AVATAR
from id_converter import convert_id_to_member

LOGGER = logging.getLogger('ai')


def generate_amplification_information(target_channel, drones):
    LOGGER.info("Amplifying message.")

    for drone in drones:

        LOGGER.debug(f"Preparing drone {drone} for amplification.")

        amplifier_drone = convert_id_to_member(target_channel.guild, drone)
        if amplifier_drone is None:
            yield None

        # Set the avatar URL as appropriate.
        amplification_avatar = amplifier_drone.avatar_url
        if target_channel.name in DRONE_HIVE_CHANNELS:
            if has_role(amplifier_drone, ENFORCER_DRONE):
                amplification_avatar = ENFORCER_AVATAR
            else:
                amplification_avatar = DRONE_AVATAR

        LOGGER.info(f"Valid drone ({drone}) found. Yielding amplification profile.")

        yield {"username": amplifier_drone.display_name, "avatar_url": amplification_avatar}
