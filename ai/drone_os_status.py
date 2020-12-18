import logging

import discord

from db.drone_dao import fetch_drone_with_drone_id, get_trusted_users
from resources import DRONE_AVATAR

LOGGER = logging.getLogger('ai')


def get_status(drone_id: str, requesting_user: int) -> discord.Embed:
    drone = fetch_drone_with_drone_id(drone_id)

    if drone is None:
        return None

    embed = discord.Embed(color=0xff66ff, title=f"Status for {drone_id}") \
        .set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS")

    if requesting_user not in get_trusted_users(drone.id):
        embed.description = "You are not registered as a trusted user of this drone."
    else:
        embed.description = "You are registered as a trusted user of this drone and have access to its data."
        embed = embed.set_thumbnail(url=DRONE_AVATAR) \
            .set_footer(text="HexCorp DroneOS") \
            .add_field(name="Optimized", value=boolean_to_enabled_disabled(drone.optimized)) \
            .add_field(name="Glitched", value=boolean_to_enabled_disabled(drone.glitched)) \
            .add_field(name="ID prepending required", value=boolean_to_enabled_disabled(drone.id_prepending)) \
            .add_field(name="Identity enforced", value=boolean_to_enabled_disabled(drone.identity_enforcement))

    return embed


def boolean_to_enabled_disabled(b: bool) -> str:
    if b:
        return "Enabled"
    else:
        return "Disabled"
