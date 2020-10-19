import unittest
from unittest.mock import AsyncMock, patch
from ai.trusted_user import add_trusted_user, remove_trusted_user
from resources import HIVE_MXTRESS_USER_ID


class TrustedUserTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.hive_mxtress = AsyncMock()
        self.hive_mxtress.id = HIVE_MXTRESS_USER_ID
        self.hive_mxtress.display_name = "Hive Mxtress"

        self.drone_member = AsyncMock()
        self.drone_member.id = "7214376142"
        self.drone_member.display_name = "⬡-Drone #3287"

        self.trusted_user_member = AsyncMock()
        self.trusted_user_member.id = "872635821"
        self.trusted_user_member.display_name = "⬡-Drone #9813"

        self.context = AsyncMock()
        self.context.bot.guilds[0].members = [self.drone_member, self.trusted_user_member, self.hive_mxtress]
        self.context.author.id = self.drone_member.id
        self.context.bot.guilds[0].get_member.return_value = self.drone_member

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_successful_add(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await add_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author, [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id])
        self.context.send.assert_called_once_with(f"Successfully added trusted user \"{self.trusted_user_member.display_name}\"")
        self.context.bot.guilds[0].get_member.assert_called_once_with(self.drone_member.id)
        self.trusted_user_member.send.assert_called_once_with(f"You were added as a trusted user by \"{self.drone_member.display_name}\".\nIf you believe this to be a mistake contact the drone in question or the moderation team.")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_already_trusted(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id]

        # run
        await add_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with(f"User with name \"{self.trusted_user_member.display_name}\" is already trusted")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_not_a_member(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_discord_id_of_drone.return_value = None

        # run
        await add_trusted_user(self.context, "Some random name")

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with("No user with name \"Some random name\" found")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_add_yourself(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup

        # run
        await add_trusted_user(self.context, self.drone_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with("Can not add yourself to your list of trusted users")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_successful_remove(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author, [HIVE_MXTRESS_USER_ID])
        self.context.send.assert_called_once_with(f"Successfully removed trusted user \"{self.trusted_user_member.display_name}\"")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_remove_not_trusted(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with(f"User with name \"{self.trusted_user_member.display_name}\" was not trusted")

    @patch("ai.trusted_user.get_discord_id_of_drone")
    @patch("ai.trusted_user.get_trusted_users")
    @patch("ai.trusted_user.set_trusted_users")
    async def test_remove_hive_mxtress(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await remove_trusted_user(self.context, "Hive Mxtress")

        # assert
        set_trusted_users.assert_not_called()
        self.context.send.assert_called_once_with("Can not remove the Hive Mxtress as a trusted user")
