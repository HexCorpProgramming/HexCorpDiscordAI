import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai.temporary_dronification import TemporaryDronificationCog, DronificationRequest
import test.test_utils as test_utils
from test.cog import cog
from test.mocks import Mocks


class TestTemporaryDronification(unittest.IsolatedAsyncioTestCase):

    initiator: MagicMock
    mocks: Mocks

    @cog(TemporaryDronificationCog)
    async def asyncSetUp(self, mocks: Mocks) -> None:
        self.mocks = mocks
        mocks.get_cog().dronification_requests = []
        self.initiator = self.mocks.drone_member('1234')

    async def test_request_dronification(self) -> None:
        target = self.mocks.drone_member('5678', drone=None)
        message = self.mocks.command(self.initiator, '', f'temporarily_dronify {target.mention} 4')

        await self.assert_command_successful(message)

        self.mocks.get_bot().context.reply.assert_called_once_with(f"Target identified and locked on. Commencing temporary dronification procedure. {target.mention} you have 5 minutes to comply by replying to this message. Do you consent? (y/n)")
        requests = self.mocks.get_cog().dronification_requests
        self.assertEqual(1, len(requests), "There must be exactly one dronification request.")
        self.assertEqual(target, requests[0].target)
        self.assertEqual(self.initiator, requests[0].issuer)
        self.assertEqual(4, requests[0].hours)

    async def expect_error(self, target: MagicMock, error: str, hours: int = 4) -> None:
        message = self.mocks.command(self.initiator, '', f'temporarily_dronify {target.mention} ' + str(hours))

        await self.assert_command_error(message, error)

        self.assertEqual(0, len(self.mocks.get_cog().dronification_requests), "There must be no dronification requests.")

    async def test_request_dronification_already_drone(self) -> None:
        target = self.mocks.drone_member('5678')
        await self.expect_error(target, 'Drone-5678 is already a drone.')

    async def test_request_dronification_hive_mxtress(self) -> None:
        target = self.mocks.hive_mxtress()
        await self.expect_error(target, 'The Hive Mxtress is not a valid target for temporary dronification.')

    async def test_request_dronification_hours_negative(self) -> None:
        target = self.mocks.drone_member('5678', drone=None)
        await self.expect_error(target, 'Hours must be greater than 0.', -4)

    async def test_request_not_24_hours(self) -> None:
        target = self.mocks.drone_member('5678', drone=None, joined_at=datetime.now(timezone.utc) - timedelta(hours=16))
        await self.expect_error(target, 'Target has not been on the server for more than 24 hours. Can not temporarily dronify.')

    @patch("src.ai.temporary_dronification.create_drone")
    async def test_temporary_dronification_response(self, create_drone: AsyncMock) -> None:
        # Inject a pending request.
        hours = 4
        target = self.mocks.drone_member('5678', drone=None)
        question_message = self.mocks.message()
        request = DronificationRequest(target, self.initiator, hours, question_message)
        self.mocks.get_cog().dronification_requests.append(request)

        message = self.mocks.message(target, '', 'y')
        message.reference.resolved = question_message

        await self.mocks.get_cog().temporary_dronification_response(message)

        create_drone.assert_called_once()
        self.assertEqual(message.guild, create_drone.call_args.args[0])
        self.assertEqual(message.author, create_drone.call_args.args[1])
        self.assertEqual(message.channel, create_drone.call_args.args[2])
        self.assertEqual([str(self.initiator.id)], create_drone.call_args.args[3])
        self.assertAlmostEqual((datetime.now() + timedelta(hours=hours)).timestamp(), create_drone.call_args.args[4].timestamp(), delta=1)
        self.assertEqual(0, len(self.mocks.get_cog().dronification_requests))
        message.reply.assert_called_once_with(f"Consent noted. HexCorp dronification suite engaged for the next {hours} hours.")

    @patch("src.ai.temporary_dronification.create_drone")
    async def test_temporary_dronification_declined(self, create_drone: AsyncMock) -> None:
        target = self.mocks.drone_member('5678', drone=None)

        # Inject a pending request.
        hours = 4
        question_message = self.mocks.message()
        request = DronificationRequest(target, self.initiator, hours, question_message)
        self.mocks.get_cog().dronification_requests.append(request)

        message = self.mocks.message(target, '', 'n')
        message.reference.resolved = question_message

        await self.mocks.get_cog().temporary_dronification_response(message)

        create_drone.assert_not_called()

    @patch('src.ai.temporary_dronification.fetch_all_elapsed_temporary_dronification')
    async def test_release_temporary_drones(self, fetch_all_elapsed_temporary_dronification) -> None:
        member = self.mocks.drone_member('5555')
        fetch_all_elapsed_temporary_dronification.return_value = [member.drone]

        await test_utils.start_and_await_loop(self.mocks.get_cog().release_temporary_drones)

        member.drone.delete.assert_called_once()
