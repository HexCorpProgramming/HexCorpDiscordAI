import unittest
from unittest.mock import AsyncMock, patch, Mock
from src.ai.trusted_user import TrustedUserCog, TrustedUserRequest, find_user_by_display_name_or_drone_id, remove_trusted_user, remove_trusted_user_on_all
from src.resources import HIVE_MXTRESS_USER_ID


class TrustedUserTest(unittest.IsolatedAsyncioTestCase):

    bot = AsyncMock()
    cog = TrustedUserCog(bot)

    def setUp(self):
        self.hive_mxtress = AsyncMock()
        self.hive_mxtress.id = HIVE_MXTRESS_USER_ID
        self.hive_mxtress.display_name = "Hive Mxtress"

        self.drone_member = AsyncMock()
        self.drone_member.id = "7214376142"
        self.drone_member.display_name = "⬡-Drone #3287"
        self.drone_member.name = "Drone 3287"

        self.trusted_user_member = AsyncMock()
        self.trusted_user_member.id = "872635821"
        self.trusted_user_member.display_name = "⬡-Drone #9813"
        self.trusted_user_member.name = "Drone 9813"

        self.context = AsyncMock()
        self.context.bot.guilds[0].members = [self.drone_member, self.trusted_user_member, self.hive_mxtress]
        self.context.author.id = self.drone_member.id
        self.context.bot.guilds[0].get_member.return_value = self.drone_member

        self.cog.trusted_user_requests = []

    def test_successful_find_user_by_display_name(self):
        # setup
        # run
        found_user = find_user_by_display_name_or_drone_id(self.trusted_user_member.display_name, self.context.bot.guilds[0])

        # assert
        self.assertEqual(self.trusted_user_member, found_user)

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    def test_successful_find_user_by_drone_id(self, get_discord_id_of_drone):
        # setup
        get_discord_id_of_drone.return_value = self.drone_member.id

        # run
        found_user = find_user_by_display_name_or_drone_id("3287", self.context.bot.guilds[0])

        # assert
        self.assertEqual(self.drone_member, found_user)
        get_discord_id_of_drone.assert_called_once_with("3287")

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    def test_unsuccessful_find_user_by_display_name_or_drone_id(self, get_discord_id_of_drone):
        # setup
        get_discord_id_of_drone.return_value = None

        # run
        found_user = find_user_by_display_name_or_drone_id("0000", self.context.bot.guilds[0])

        # assert
        self.assertIsNone(found_user)

    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.find_user_by_display_name_or_drone_id")
    async def test_successful_request(self, find_user_by_display_name_or_drone_id, get_trusted_users):
        # setup
        find_user_by_display_name_or_drone_id.return_value = self.trusted_user_member
        get_trusted_users.return_value = [int(self.hive_mxtress.id)]

        question_message = AsyncMock()
        question_message.id = 123456
        question_message_id = question_message.id
        self.trusted_user_member.send.return_value = question_message
        self.context.author = self.drone_member

        # run
        await self.cog.add_trusted_user(self.cog, self.context, self.trusted_user_member.name)

        # assert
        self.trusted_user_member.send.assert_called_once_with("\"⬡-Drone #3287\" is requesting to add you as a trusted user. This request will expire in 24 hours. To accept or reject this request, reply to this message. (y/n)")
        self.context.reply.assert_called_once_with("Request sent to \"⬡-Drone #9813\". They have 24 hours to accept.")
        self.assertEqual(1, len(self.cog.trusted_user_requests))
        self.assertEqual(self.trusted_user_member, self.cog.trusted_user_requests[0].target)
        self.assertEqual(self.drone_member, self.cog.trusted_user_requests[0].issuer)
        self.assertEqual(question_message_id, self.cog.trusted_user_requests[0].question_message_id)

    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.find_user_by_display_name_or_drone_id")
    async def test_unsuccessful_request_user_not_found(self, find_user_by_display_name_or_drone_id, get_trusted_users):
        # setup
        find_user_by_display_name_or_drone_id.return_value = None
        get_trusted_users.return_value = [self.hive_mxtress.id]

        # run
        await self.cog.add_trusted_user(self.cog, self.context, self.trusted_user_member.name)

        # assert
        self.context.reply.assert_called_once_with("No user with name \"Drone 9813\" found.")
        self.trusted_user_member.send.assert_not_called()
        self.assertEqual(0, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.find_user_by_display_name_or_drone_id")
    async def test_unsuccessful_request_user_is_self(self, find_user_by_display_name_or_drone_id, get_trusted_users):
        # setup
        find_user_by_display_name_or_drone_id.return_value = self.drone_member
        get_trusted_users.return_value = [self.hive_mxtress.id]
        self.context.author = self.drone_member

        # run
        await self.cog.add_trusted_user(self.cog, self.context, self.trusted_user_member.name)

        # assert
        self.context.reply.assert_called_once_with("Can not add yourself to your list of trusted users.")
        self.trusted_user_member.send.assert_not_called()
        self.assertEqual(0, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.find_user_by_display_name_or_drone_id")
    async def test_unsuccessful_request_user_already_added(self, find_user_by_display_name_or_drone_id, get_trusted_users):
        # setup
        find_user_by_display_name_or_drone_id.return_value = self.trusted_user_member
        get_trusted_users.return_value = [self.trusted_user_member.id]
        self.context.author = self.drone_member

        # run
        await self.cog.add_trusted_user(self.cog, self.context, self.trusted_user_member.name)

        # assert
        self.context.reply.assert_called_once_with("User with name \"⬡-Drone #9813\" is already trusted.")
        self.trusted_user_member.send.assert_not_called()
        self.assertEqual(0, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.set_trusted_users")
    @patch("src.ai.trusted_user.get_trusted_users")
    async def test_trusted_user_response_accepted(self, get_trusted_users, set_trusted_users):
        # setup
        question_message_id = AsyncMock()

        target = self.trusted_user_member
        issuer = self.drone_member

        request = TrustedUserRequest(target, issuer, question_message_id)

        self.cog.trusted_user_requests.append(request)

        message = AsyncMock()
        message.content = "y"
        message.reference.message.id = question_message_id
        message.reference.resolved.id = question_message_id
        message.author = target
        message.guild = AsyncMock()

        # run
        await self.cog.trusted_user_response(message, None)

        # assert
        get_trusted_users.assert_called_once_with(request.issuer.id)
        set_trusted_users.assert_called_once()
        message.reply.assert_called_once_with("Consent noted. You have been added as a trusted user of \"⬡-Drone #3287\".")
        request.issuer.send.assert_called_once_with("\"⬡-Drone #9813\" has accepted your request and is now a trusted user.")
        self.assertEqual(0, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.set_trusted_users")
    @patch("src.ai.trusted_user.get_trusted_users")
    async def test_trusted_user_response_rejected(self, get_trusted_users, set_trusted_users):
        # setup
        question_message_id = AsyncMock()

        target = self.trusted_user_member
        issuer = self.drone_member

        request = TrustedUserRequest(target, issuer, question_message_id)

        self.cog.trusted_user_requests.append(request)

        message = AsyncMock()
        message.content = "n"
        message.reference.message_id = question_message_id
        message.reference.resolved.id = question_message_id
        message.author = target
        message.guild = AsyncMock()

        # run
        await self.cog.trusted_user_response(message, None)

        # assert
        get_trusted_users.assert_not_called()
        set_trusted_users.assert_not_called()
        message.reply.assert_called_once_with("Consent not given. You have not been added as a trusted user of \"⬡-Drone #3287\".")
        request.issuer.send.assert_called_once_with("\"⬡-Drone #9813\" has rejected your request. No changes have been made.")
        self.assertEqual(0, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.set_trusted_users")
    @patch("src.ai.trusted_user.get_trusted_users")
    async def test_trusted_user_response_invalid(self, get_trusted_users, set_trusted_users):
        # setup
        question_message_id = AsyncMock()

        target = self.trusted_user_member
        issuer = self.drone_member

        request = TrustedUserRequest(target, issuer, question_message_id)

        self.cog.trusted_user_requests.append(request)

        message = AsyncMock()
        message.content = "bingle"
        message.reference.message_id = question_message_id
        message.reference.resolved.id = question_message_id
        message.author = target
        message.guild = AsyncMock()

        # run
        await self.cog.trusted_user_response(message, None)

        # assert
        get_trusted_users.assert_not_called()
        set_trusted_users.assert_not_called()
        message.reply.assert_not_called()
        request.issuer.send.assert_not_called()
        self.assertEqual(1, len(self.cog.trusted_user_requests))

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.set_trusted_users")
    async def test_successful_remove_by_display_name(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author.id, [HIVE_MXTRESS_USER_ID])
        self.context.reply.assert_called_once_with(f"Successfully removed trusted user \"{self.trusted_user_member.display_name}\".")

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.set_trusted_users")
    async def test_successful_remove_by_user_name(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_called_once_with(self.context.author.id, [HIVE_MXTRESS_USER_ID])
        self.context.reply.assert_called_once_with(
            f"Successfully removed trusted user \"{self.trusted_user_member.display_name}\".")

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.set_trusted_users")
    async def test_remove_not_trusted(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await remove_trusted_user(self.context, self.trusted_user_member.display_name)

        # assert
        set_trusted_users.assert_not_called()
        self.context.reply.assert_called_once_with(f"User with name \"{self.trusted_user_member.display_name}\" was not trusted.")

    @patch("src.ai.trusted_user.find_user_by_display_name_or_drone_id")
    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.set_trusted_users")
    async def test_remove_not_found(self, set_trusted_users, get_trusted_users, find_user_by_display_name_or_drone_id):
        # setup
        find_user_by_display_name_or_drone_id.return_value = None
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await remove_trusted_user(self.context, "0000")

        # assert
        set_trusted_users.assert_not_called()
        self.context.reply.assert_called_once_with("No user with name \"0000\" found.")

    @patch("src.ai.trusted_user.get_discord_id_of_drone")
    @patch("src.ai.trusted_user.get_trusted_users")
    @patch("src.ai.trusted_user.set_trusted_users")
    async def test_remove_hive_mxtress(self, set_trusted_users, get_trusted_users, get_discord_id_of_drone):
        # setup
        get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID]

        # run
        await remove_trusted_user(self.context, "Hive Mxtress")

        # assert
        set_trusted_users.assert_not_called()
        self.context.reply.assert_called_once_with("Can not remove the Hive Mxtress as a trusted user.")

    @patch("src.ai.trusted_user.set_trusted_users")
    @patch("src.ai.trusted_user.fetch_all_drones_with_trusted_user")
    async def test_remove_trusted_user_on_all(self, fetch_all_drones_with_trusted_user, set_trusted_users):
        # setup
        id_of_member_leaving = 9347598344357

        unrelated_user_id = 12405280928135

        drone = Mock()
        drone.id = 8346759834
        drone.trusted_users = f"{HIVE_MXTRESS_USER_ID}|{id_of_member_leaving}|{unrelated_user_id}"

        fetch_all_drones_with_trusted_user.return_value = [drone]

        # run
        remove_trusted_user_on_all(id_of_member_leaving)

        # assert
        fetch_all_drones_with_trusted_user.assert_called_once_with(id_of_member_leaving)
        set_trusted_users.assert_called_once_with(drone.id, [int(HIVE_MXTRESS_USER_ID), unrelated_user_id])

    @patch("src.ai.trusted_user.remove_trusted_user")
    async def test_remove_trusted_user_command(self, remove_trusted_user):
        # setup

        # run
        await self.cog.remove_trusted_user(self.cog, self.context, self.trusted_user_member.name)

        # assert
        remove_trusted_user.assert_called_once()
