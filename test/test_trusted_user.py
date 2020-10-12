import unittest
from unittest.mock import AsyncMock, patch
from ai.trusted_user import add_trusted_user, remove_trusted_user


class TrustedUserTes(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.drone_member = AsyncMock()
        self.drone_member.id = 7214376142
        self.drone_member.display_name = "⬡-Drone #3287"

        self.trusted_user_member = AsyncMock()
        self.trusted_user_member.id = 872635821
        self.trusted_user_member.display_name = "⬡-Drone #9813"

        self.trusted_user_dm = AsyncMock()
        self.trusted_user_member.create_dm = AsyncMock(return_value=self.trusted_user_dm)

        self.context = AsyncMock()
        self.context.bot.guilds[0].members = [self.drone_member, self.trusted_user_member]
        self.context.author.id = self.drone_member.id
        self.context.bot.guilds[0].get_member.return_value = self.drone_member

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_successful_add(self, set_trusted_users, get_trusted_users):
        # setup
        get_trusted_users.return_value = []

        # run
        await add_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author, [self.trusted_user_member.id])
        self.context.send.assert_called_once_with(f"Successfully added trusted user \"{self.trusted_user_member.display_name}\"")
        self.context.bot.guilds[0].get_member.assert_called_once_with(self.drone_member.id)
        self.trusted_user_dm.send.assert_called_once_with(f"You were added as a trusted user by \"{self.drone_member.display_name}\".\nIf you believe this to be a mistake contact the drone in question or the moderation team.")

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_already_trusted(self, set_trusted_users, get_trusted_users):
        # setup
        get_trusted_users.return_value = [self.trusted_user_member.id]

        # run
        await add_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with(f"User with name \"{self.trusted_user_member.display_name}\" is already trusted")

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_not_a_member(self, set_trusted_users, get_trusted_users):
        # setup

        # run
        await add_trusted_user(self.context, "Some random name")

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with("No user with name \"Some random name\" found")

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_add_yourself(self, set_trusted_users, get_trusted_users):
        # setup

        # run
        await add_trusted_user(self.context, self.drone_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with("Can not add yourself to your list of trusted users")

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_successful_remove(self, set_trusted_users, get_trusted_users):
        # setup
        get_trusted_users.return_value = [self.trusted_user_member.id]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author, [])
        self.context.send.assert_called_once_with(f"Successfully removed trusted user \"{self.trusted_user_member.display_name}\"")

    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_remove_not_trusted(self, set_trusted_users, get_trusted_users):
        # setup
        get_trusted_users.return_value = []

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with(f"User with name \"{self.trusted_user_member.display_name}\" was not trusted")
