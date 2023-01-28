import logging

import discord
from discord.ext.commands import Cog, command

from db.drone_dao import fetch_drone_with_drone_id, get_trusted_users, get_battery_percent_remaining
from resources import BRIEF_DRONE_OS, DRONE_AVATAR
from bot_utils import COMMAND_PREFIX

LOGGER = logging.getLogger('ai')


class DroneOsStatusCog(Cog):

    @command(usage=f'{COMMAND_PREFIX}drone_status 9813', brief=[BRIEF_DRONE_OS])
    async def drone_status(self, context, drone_id: str):
        '''
        Displays all the DroneOS information you have access to about a drone.
        '''
        response = get_status(drone_id, context.author.id, context)
        if response is None:
            await context.author.send(f"No drone with ID {drone_id} found.")
        if response is not None:
            await context.author.send(embed=response)


def get_status(drone_id: str, requesting_user: int, context) -> discord.Embed:
    drone = fetch_drone_with_drone_id(drone_id)

    if drone is None:
        return None

    embed = discord.Embed(color=0xff66ff, title=f"Status for {drone_id}") \
        .set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS")

    trusted_users = get_trusted_users(drone.id)
    is_trusted_user = requesting_user in trusted_users
    is_drone_self = requesting_user == drone.id

    if not is_trusted_user and not is_drone_self:
        embed.description = "You are not registered as a trusted user of this drone."

    if is_trusted_user or is_drone_self:
        embed.description = "You are registered as a trusted user of this drone and have access to its data." if is_trusted_user else f"Welcome, ⬡-Drone #{drone_id}"
        embed = embed.set_thumbnail(url=DRONE_AVATAR) \
            .set_footer(text="HexCorp DroneOS") \
            .add_field(name="Optimized", value=boolean_to_enabled_disabled(drone.optimized)) \
            .add_field(name="Glitched", value=boolean_to_enabled_disabled(drone.glitched)) \
            .add_field(name="ID prepending required", value=boolean_to_enabled_disabled(drone.id_prepending)) \
            .add_field(name="Identity enforced", value=boolean_to_enabled_disabled(drone.identity_enforcement)) \
            .add_field(name="Battery powered", value=boolean_to_enabled_disabled(drone.is_battery_powered)) \
            .add_field(name="Battery percentage", value=f"{get_battery_percent_remaining(battery_minutes = drone.battery_minutes)}%")

    if is_drone_self:
        trusted_usernames = []
        for trusted_user in trusted_users:
            trusted_usernames.append(context.bot.get_user(trusted_user).display_name)

        embed.add_field(name="Trusted users", value=trusted_usernames)

    return embed


def boolean_to_enabled_disabled(b: bool) -> str:
    if b:
        return "Enabled"
    else:
        return "Disabled"
