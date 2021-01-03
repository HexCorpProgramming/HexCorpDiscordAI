import logging

import discord
from discord.ext.commands import dm_only, Cog, command

from db.drone_dao import fetch_drone_with_drone_id, get_trusted_users
from resources import DRONE_AVATAR
from bot_utils import COMMAND_PREFIX

LOGGER = logging.getLogger('ai')


class DroneOsStatusCog(Cog):

    @dm_only()
    @command(usage=f'{COMMAND_PREFIX}drone_status 9813', brief="DroneOS")
    async def drone_status(self, context, drone_id: str):
        '''
        Displays all the DroneOS information you have access to about a drone.
        '''
        response = get_status(drone_id, context.author.id)
        if response is None:
            await context.send(f"No drone with ID {drone_id} found.")
        if response is not None:
            await context.send(embed=response)


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
