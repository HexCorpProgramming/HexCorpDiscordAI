import discord
from discord.ext.commands import Cog, command, Context, UserInputError

from src.resources import BRIEF_DRONE_OS, DRONE_AVATAR
from src.bot_utils import COMMAND_PREFIX
from src.roles import MODERATION_ROLES, has_any_role
from src.drone_member import DroneMember
from src.log import log


class DroneOsStatusCog(Cog):

    @command(usage=f'{COMMAND_PREFIX}drone_status 9813', brief=[BRIEF_DRONE_OS])
    async def drone_status(self, context, member: DroneMember):
        '''
        Displays all the DroneOS information you have access to about a drone.
        '''
        response = await get_status(member, context)

        if response is None:
            raise UserInputError('The specified member is not a drone')

        log.info('Sending DroneOS status')
        await context.author.send(embed=response)


async def get_status(member: DroneMember, context: Context) -> discord.Embed:
    drone = member.drone

    if drone is None:
        raise UserInputError('The specified member is not a drone')

    embed = discord.Embed(color=0xff66ff, title=f"Status for {drone.drone_id}") \
        .set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS")

    author = context.author if isinstance(context.author, discord.Member) else context.bot.guilds[0].get_member(context.author.id)

    is_trusted_user = drone.trusts(author)
    is_drone_self = author.id == member.id
    is_moderation = has_any_role(author, MODERATION_ROLES)

    # return early when this request is not authorized
    if not is_trusted_user and not is_drone_self and not is_moderation:
        raise UserInputError("You are not registered as a trusted user of this drone.")

    battery_type = drone.battery_type

    # assemble description
    if is_trusted_user:
        embed.description = "You are registered as a trusted user of this drone and have access to its data."
    if is_moderation:
        embed.description = "You are a moderator and have access to this drone's data."
    if is_drone_self:
        embed.description = f"Welcome, ⬡-Drone #{drone.drone_id}"

    # assemble embed content
    embed = embed.set_thumbnail(url=DRONE_AVATAR) \
        .set_footer(text="HexCorp DroneOS") \
        .add_field(name="Optimized", value=boolean_to_enabled_disabled(drone.optimized)) \
        .add_field(name="Glitched", value=boolean_to_enabled_disabled(drone.glitched)) \
        .add_field(name="ID prepending required", value=boolean_to_enabled_disabled(drone.id_prepending)) \
        .add_field(name="Identity enforced", value=boolean_to_enabled_disabled(drone.identity_enforcement)) \
        .add_field(name="Battery powered", value=boolean_to_enabled_disabled(drone.is_battery_powered)) \
        .add_field(name="Battery type", value=battery_type.name)\
        .add_field(name="Battery percentage", value=f"{drone.get_battery_percent_remaining()}%")\
        .add_field(name="Free storage", value=boolean_to_enabled_disabled(drone.free_storage))

    # create list of trusted users
    if is_drone_self:
        trusted_usernames = []
        for trusted_user_id in drone.trusted_users:
            trusted_user = context.guld.get_member(trusted_user_id)

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
