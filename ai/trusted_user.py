import logging


from db.drone_dao import get_trusted_users, set_trusted_users

LOGGER = logging.getLogger('ai')


async def add_trusted_user(context, trusted_user_id: int):
    trusted_users = get_trusted_users(context.author)

    if trusted_user_id in trusted_users:
        await context.send("User with given ID is already trusted")
        return

    trusted_users.append(trusted_user_id)
    set_trusted_users(context.author, trusted_users)
    await context.send("Successfully added trusted user")
