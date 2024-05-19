import unittest
from unittest.mock import AsyncMock, patch, Mock
from test.mocks import Mocks

from datetime import datetime, timedelta, timezone

import src.roles as roles
import src.ai.assign as assign
from src.channels import ASSIGNMENT_CHANNEL


associate_role = Mock()
associate_role.name = roles.ASSOCIATE
drone_role = Mock()
drone_role.name = roles.DRONE
hive_mxtress_role = Mock()
hive_mxtress_role.name = roles.HIVE_MXTRESS


class AssignmentTest(unittest.IsolatedAsyncioTestCase):

    async def test_request_reject(self):
        mocks = Mocks()
        message = mocks.message(None, ASSIGNMENT_CHANNEL, 'Beep Boop want to be drone!')

        self.assertTrue(await assign.check_for_assignment_message(message))
        message.delete.assert_called_once()

    async def test_wrong_channel(self):
        mocks = Mocks()
        message = mocks.message(None, 'general', assign.ASSIGNMENT_MESSAGE)

        self.assertFalse(await assign.check_for_assignment_message(message))
        message.delete.assert_not_called()

    @patch("src.ai.assign.get_used_drone_ids", new_callable=AsyncMock)
    @patch("src.ai.assign.BatteryType", new_callable=AsyncMock)
    @patch("src.ai.assign.Drone")
    async def test_request_approve(self, Drone: Mock, BatteryType: AsyncMock, get_used_drone_ids: AsyncMock):
        mocks = Mocks()
        author = mocks.member('User 1234')
        message = mocks.message(author, ASSIGNMENT_CHANNEL, assign.ASSIGNMENT_MESSAGE)

        get_used_drone_ids.return_value = []
        Drone.return_value = mocks.drone(1234)
        BatteryType.load.return_value = mocks.battery_type()

        self.assertTrue(await assign.check_for_assignment_message(message))
        Drone.return_value.insert.assert_called_once()

        author.remove_roles.assert_called_once_with(mocks.role(roles.ASSOCIATE))
        author.add_roles.assert_called_once_with(mocks.role(roles.DRONE))
        author.edit.assert_called_once_with(nick="⬡-Drone #1234")

    @patch("src.ai.assign.get_used_drone_ids", new_callable=AsyncMock)
    @patch("src.ai.assign.BatteryType", new_callable=AsyncMock)
    @patch("src.ai.assign.Drone")
    async def test_assign_hive_mxtress(self, Drone: Mock, BatteryType: AsyncMock, get_used_drone_ids: AsyncMock):
        mocks = Mocks()
        author = mocks.member('Hive Mxtress', roles=[roles.HIVE_MXTRESS])
        message = mocks.message(author, ASSIGNMENT_CHANNEL, assign.ASSIGNMENT_MESSAGE)

        get_used_drone_ids.return_value = []
        drone = mocks.drone('0006')
        Drone.return_value = drone
        BatteryType.load.return_value = mocks.battery_type()

        self.assertTrue(await assign.check_for_assignment_message(message))

        drone.insert.assert_called_once()
        self.assertEqual(drone.drone_id, '0006')

        author.remove_roles.assert_called_once_with(mocks.role(roles.ASSOCIATE))
        author.add_roles.assert_called_once_with(mocks.role(roles.DRONE))

    @patch("src.ai.assign.get_used_drone_ids", new=AsyncMock(return_value=["1234"]))
    async def test_id_already_used2(self):
        mocks = Mocks()
        author = mocks.member('User 1234')
        message = mocks.message(author, ASSIGNMENT_CHANNEL, assign.ASSIGNMENT_MESSAGE)

        self.assertTrue(await assign.check_for_assignment_message(message))
        message.channel.send.assert_called_once_with(f'{author.mention}: ID 1234 present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')

    async def test_too_early(self):
        mocks = Mocks()
        author = mocks.member('User 1234', joined_at=datetime.now(timezone.utc) - timedelta(hours=20))
        message = mocks.message(author, ASSIGNMENT_CHANNEL, assign.ASSIGNMENT_MESSAGE)

        self.assertFalse(await assign.check_for_assignment_message(message))
        message.channel.send.assert_called_once_with("Invalid request, associate must have existed on the server for at least 24 hours before dronification.")
