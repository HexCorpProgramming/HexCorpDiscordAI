import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, Mock
from ai.temporary_dronification import TemporaryDronificationCog, DronificationRequest
from roles import HIVE_MXTRESS


class TestSpeechOptimization(unittest.IsolatedAsyncioTestCase):

    bot = AsyncMock()
    cog = TemporaryDronificationCog(bot)

    def setUp(self):
        self.bot.reset_mock()
        self.cog.dronfication_requests = []

    @patch("ai.temporary_dronification.is_drone")
    async def test_request_dronification(self, is_drone):
        # init
        question_message = AsyncMock()

        context = AsyncMock()
        context.reply.return_value = question_message

        target = AsyncMock()
        target.mention = "Target Associate"
        target.joined_at = datetime.now() - timedelta(hours=48)

        hours = 4

        is_drone.return_value = False

        # run
        await self.cog.temporarily_dronify(self.cog, context, target, hours)

        # assert
        is_drone.assert_called_once_with(target)
        context.reply.assert_called_once_with(f"Target identified and locked on. Commencing temporary dronification procedure. {target.mention} you have 5 minutes to comply by replying to this message. Do you consent? (y/n)")
        self.assertEqual(1, len(self.cog.dronfication_requests), "There must be exactly one dronification request.")
        self.assertEqual(target, self.cog.dronfication_requests[0].target)
        self.assertEqual(context.author, self.cog.dronfication_requests[0].issuer)
        self.assertEqual(hours, self.cog.dronfication_requests[0].hours)
        self.assertEqual(question_message, self.cog.dronfication_requests[0].question_message)

    @patch("ai.temporary_dronification.is_drone")
    async def test_request_dronification_already_drone(self, is_drone):
        # init
        question_message = AsyncMock()

        context = AsyncMock()
        context.reply.return_value = question_message

        target = AsyncMock()
        target.mention = "Target Associate"

        hours = 4

        is_drone.return_value = True

        # run
        await self.cog.temporarily_dronify(self.cog, context, target, hours)

        # assert
        is_drone.assert_called_once_with(target)
        context.reply.assert_called_once_with(f"{target.display_name} is already a drone.")
        self.assertEqual(0, len(self.cog.dronfication_requests), "There must be no dronification requests.")

    @patch("ai.temporary_dronification.is_drone")
    async def test_request_dronification_hive_mxtress(self, is_drone):
        # init
        question_message = AsyncMock()

        context = AsyncMock()
        context.reply.return_value = question_message

        target = AsyncMock()
        target.mention = "Target Associate"

        hive_mxtress_role = Mock()
        hive_mxtress_role.name = HIVE_MXTRESS
        target.roles = [hive_mxtress_role]

        hours = 4

        is_drone.return_value = False

        # run
        await self.cog.temporarily_dronify(self.cog, context, target, hours)

        # assert
        is_drone.assert_called_once_with(target)
        context.reply.assert_called_once_with("The Hive Mxtress is not a valid target for temporary dronification.")
        self.assertEqual(0, len(self.cog.dronfication_requests), "There must be no dronification request.")

    @patch("ai.temporary_dronification.is_drone")
    async def test_request_dronification_hours_negative(self, is_drone):
        # init
        question_message = AsyncMock()

        context = AsyncMock()
        context.reply.return_value = question_message

        target = AsyncMock()
        target.mention = "Target Associate"

        hours = -4

        is_drone.return_value = False

        # run
        await self.cog.temporarily_dronify(self.cog, context, target, hours)

        # assert
        context.reply.assert_called_once_with("Hours must be greater than 0.")
        self.assertEqual(0, len(self.cog.dronfication_requests), "There must be no dronification request.")

    @patch("ai.temporary_dronification.is_drone")
    async def test_request_not_24_hours(self, is_drone):
        # init
        question_message = AsyncMock()

        context = AsyncMock()
        context.reply.return_value = question_message

        target = AsyncMock()
        target.mention = "Target Associate"
        target.joined_at = datetime.now() - timedelta(hours=16)

        hours = 4

        is_drone.return_value = False

        # run
        await self.cog.temporarily_dronify(self.cog, context, target, hours)

        # assert
        is_drone.assert_called_once_with(target)
        context.reply.assert_called_once_with("Target has not been on the server for more than 24 hours. Can not temporarily dronify.")
        self.assertEqual(0, len(self.cog.dronfication_requests), "There must be no dronification request.")

    @patch("ai.temporary_dronification.create_drone")
    async def test_temporary_dronification_response(self, create_drone):
        # init
        question_message = AsyncMock()

        target = AsyncMock()
        issuer = AsyncMock()

        hours = 5
        request = DronificationRequest(target, issuer, hours, question_message)

        self.cog.dronfication_requests.append(request)

        message = AsyncMock()
        message.content = "y"
        message.reference.resolved = question_message
        message.author = target
        message.guild = AsyncMock()

        # run
        await self.cog.temporary_dronification_response(message, None)

        # assert
        create_drone.assert_called_once()
        self.assertEqual(message.guild, create_drone.call_args.args[0])
        self.assertEqual(message.author, create_drone.call_args.args[1])
        self.assertEqual(message.channel, create_drone.call_args.args[2])
        self.assertEqual([str(issuer.id)], create_drone.call_args.args[3])
        self.assertAlmostEqual((datetime.now() + timedelta(hours=hours)).timestamp(), create_drone.call_args.args[4].timestamp(), delta=1)
        self.assertEqual(0, len(self.cog.dronfication_requests))
        message.reply.assert_called_once_with(f"Consent noted. HexCorp dronification suite engaged for the next {hours} hours.")
