import logging
import re
from db.drone_dao import get_discord_id_of_drone
from channels import DRONE_HIVE_CHANNELS
from roles import ENFORCER_DRONE, has_role
from resources import DRONE_AVATAR, ENFORCER_AVATAR

LOGGER = logging.getLogger('ai')


def generate_amplification_information(target_channel, drones):
    LOGGER.info("Amplifying message.")

    print(target_channel)
    print(drones)

    for drone in drones:

        print("Iterating")

        LOGGER.debug(f"Preparing drone {drone} for amplification.")

        if not re.match(r"\d{4}", drone):
            print("Not a drone ID.")
            continue  # Skip any non-drone IDs.

        LOGGER.debug("Getting discord ID from database.")
        if (drone_from_db := get_discord_id_of_drone(drone)) is None:
            print("Not found in DB.")
            continue  # Given drone does not exist on server.

        amplifier_drone = target_channel.guild.get_member(drone_from_db.id)
        if amplifier_drone is None:
            print("Couldn't get member from guild.")
            continue  # If getting the member somehow failed (which it really shouldn't), keep calm and carry on.

        # Set the avatar URL as appropriate.
        amplification_avatar = amplifier_drone.avatar_url
        if target_channel.name in DRONE_HIVE_CHANNELS:
            if has_role(amplifier_drone, ENFORCER_DRONE):
                amplification_avatar = ENFORCER_AVATAR
            else:
                amplification_avatar = DRONE_AVATAR

        yield {"username": amplifier_drone.display_name, "avatar_url": amplification_avatar}
