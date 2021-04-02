import logging

from discord.utils import get
import discord
from discord.ext.commands import Cog, command, dm_only

from bot_utils import COMMAND_PREFIX
from db.drone_dao import get_trusted_users, set_trusted_users, get_discord_id_of_drone
from resources import HIVE_MXTRESS_USER_ID

LOGGER = logging.getLogger('ai')


class TrustedUserCog(Cog):

    @dm_only()
    @command(usage=f"{COMMAND_PREFIX}add_trusted_user \"A trusted user\"", brief="DroneOS")
    async def add_trusted_user(self, context, user_name: str):
        '''
        Add user with the given nickname as a trusted user.
        Use quotation marks if the username contains spaces.
        This command is used in DMs with the AI.
        '''
        await add_trusted_user(context, user_name)

    @dm_only()
    @command(usage=f"{COMMAND_PREFIX}remove_trusted_user \"The untrusted user\"", brief="DroneOS")
    async def remove_trusted_user(self, context, user_name: str):
        '''
        Remove a given user from the list of trusted users.
        Use quotation marks if the username contains spaces.
        This command is used in DMs with the AI.
        '''
        await remove_trusted_user(context, user_name)


async def add_trusted_user(context, trusted_user_name: str):
    trusted_user = find_user_by_display_name_or_drone_id(trusted_user_name, context.bot.guilds[0])

    if trusted_user is None:
        await context.send(f"No user with name \"{trusted_user_name}\" found")
        return

    if trusted_user.id == context.author.id:
        await context.send("Can not add yourself to your list of trusted users")
        return

    trusted_users = get_trusted_users(context.author.id)

    if trusted_user.id in trusted_users:
        await context.send(f"User with name \"{trusted_user_name}\" is already trusted")
        return

    # report back to drone
    trusted_users.append(trusted_user.id)
    set_trusted_users(context.author.id, trusted_users)
    await context.send(f"Successfully added trusted user \"{trusted_user_name}\"")

    # notify trusted user
    drone_name = context.bot.guilds[0].get_member(context.author.id).display_name
    await trusted_user.send(f"You were added as a trusted user by \"{drone_name}\".\nIf you believe this to be a mistake contact the drone in question or the moderation team.")


async def remove_trusted_user(context, trusted_user_name: str):
    trusted_user = find_user_by_display_name_or_drone_id(trusted_user_name, context.bot.guilds[0])

    if trusted_user is None:
        await context.send(f"No user with name \"{trusted_user_name}\" found")
        return

    trusted_users = get_trusted_users(context.author.id)

    if str(trusted_user.id) == HIVE_MXTRESS_USER_ID:
        await context.send("Can not remove the Hive Mxtress as a trusted user")
        return

    if trusted_user.id not in trusted_users:
        await context.send(f"User with name \"{trusted_user_name}\" was not trusted")
        return

    trusted_users.remove(trusted_user.id)
    set_trusted_users(context.author.id, trusted_users)
    await context.send(f"Successfully removed trusted user \"{trusted_user_name}\"")


def find_user_by_display_name_or_drone_id(id: str, guild: discord.Guild) -> discord.Member:
    user = get(guild.members, display_name=id)

    if user is not None:
        return user

    drone = get_discord_id_of_drone(id)
    if drone is not None:
        return guild.get_member(drone)

    return None
