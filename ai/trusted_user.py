import logging

from discord.utils import get

from db.drone_dao import get_trusted_users, set_trusted_users

LOGGER = logging.getLogger('ai')


async def add_trusted_user(context, trusted_user_name: str):
    trusted_user = get(context.bot.guilds[0].members, display_name=trusted_user_name)

    if trusted_user is None:
        await context.send(f"No user with name \"{trusted_user_name}\" found")
        return

    if trusted_user.id == context.author.id:
        await context.send("Can not add yourself to your list of trusted users")
        return

    trusted_users = get_trusted_users(context.author)

    if trusted_user.id in trusted_users:
        await context.send(f"User with name \"{trusted_user_name}\" is already trusted")
        return

    # report back to drone
    trusted_users.append(trusted_user.id)
    set_trusted_users(context.author, trusted_users)
    await context.send(f"Successfully added trusted user \"{trusted_user_name}\"")

    # notify trusted user
    drone_name = context.bot.guilds[0].get_member(context.author.id).display_name
    trusted_user_dm = await trusted_user.create_dm()
    await trusted_user_dm.send(f"You were added as a trusted user by \"{drone_name}\".\nIf you believe this to be a mistake contact the drone in question or the moderation team.")


async def remove_trusted_user(context, trusted_user_name: str):
    trusted_user = get(context.bot.guilds[0].members, display_name=trusted_user_name)

    if trusted_user is None:
        await context.send(f"No user with name \"{trusted_user_name}\" found")
        return

    trusted_users = get_trusted_users(context.author)

    if trusted_user.id not in trusted_users:
        await context.send(f"User with name \"{trusted_user_name}\" was not trusted")
        return

    trusted_users.remove(trusted_user.id)
    set_trusted_users(context.author, trusted_users)
    await context.send(f"Successfully removed trusted user \"{trusted_user_name}\"")
