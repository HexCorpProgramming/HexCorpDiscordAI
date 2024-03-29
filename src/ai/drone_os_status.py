import logging

import discord
from discord.ext.commands import Cog

from src.db.drone_dao import fetch_drone_with_drone_id, get_trusted_users, get_battery_percent_remaining
from src.resources import BRIEF_DRONE_OS, DRONE_AVATAR
from src.bot_utils import command, COMMAND_PREFIX
from src.roles import MODERATION_ROLES, has_any_role

LOGGER = logging.getLogger('ai')


class DroneOsStatusCog(Cog):

    @command(usage=f'{COMMAND_PREFIX}drone_status 9813', brief=[BRIEF_DRONE_OS])
    async def drone_status(self, context, drone_id: str):
        '''
        Displays all the DroneOS information you have access to about a drone.
        '''
        response = await get_status(drone_id, context.author.id, context)
        if response is None:
            await context.author.send(f"No drone with ID {drone_id} found.")
        if response is not None:
            await context.author.send(embed=response)


async def get_status(drone_id: str, requesting_user: int, context) -> discord.Embed:
    drone = await fetch_drone_with_drone_id(drone_id)

    if drone is None:
        return None

    embed = discord.Embed(color=0xff66ff, title=f"Status for {drone_id}") \
        .set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS")

    member = context.author if isinstance(context.author, discord.Member) else context.bot.guilds[0].get_member(context.author.id)

    trusted_users = await get_trusted_users(drone.id)
    is_trusted_user = requesting_user in trusted_users
    is_drone_self = requesting_user == drone.id
    is_moderation = has_any_role(member, MODERATION_ROLES)

    # return early when this request is not authorized
    if not is_trusted_user and not is_drone_self and not is_moderation:
        embed.description = "You are not registered as a trusted user of this drone."
        return embed

    # assemble description
    if is_trusted_user:
        embed.description = "You are registered as a trusted user of this drone and have access to its data."
    if is_moderation:
        embed.description = "You are a moderator and have access to this drone's data."
    if is_drone_self:
        embed.description = f"Welcome, ⬡-Drone #{drone_id}"

    # assemble embed content
    embed = embed.set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS") \
        .add_field(name="Optimized", value=boolean_to_enabled_disabled(drone.optimized)) \
        .add_field(name="Glitched", value=boolean_to_enabled_disabled(drone.glitched)) \
        .add_field(name="ID prepending required", value=boolean_to_enabled_disabled(drone.id_prepending)) \
        .add_field(name="Identity enforced", value=boolean_to_enabled_disabled(drone.identity_enforcement)) \
        .add_field(name="Battery powered", value=boolean_to_enabled_disabled(drone.is_battery_powered)) \
        .add_field(name="Battery percentage", value=f"{await get_battery_percent_remaining(battery_minutes = drone.battery_minutes)}%")\
        .add_field(name="Free storage", value=boolean_to_enabled_disabled(drone.free_storage))

    # create list of trusted users
    if is_drone_self:
        trusted_usernames = []
        for trusted_user_id in trusted_users:
            trusted_user = context.bot.get_user(trusted_user_id)

            # we might have a few dangling trusted users in the DB
            if trusted_user is not None:
                trusted_usernames.append(trusted_user.display_name)

        embed.add_field(name="Trusted users", value=trusted_usernames)

    return embed


def boolean_to_enabled_disabled(b: bool) -> str:
    if b:
        return "Enabled"
    else:
        return "Disabled"
