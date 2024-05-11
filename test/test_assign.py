import unittest
from unittest.mock import AsyncMock, patch, Mock

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
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]

        test_message.content = "Beep Boop want to be drone!"

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_called_once()

    async def test_wrong_channel(self):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]
        test_message.channel.name = "some other channel"

        self.assertFalse(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_not_called()

    @patch('src.db.record.change')
    @patch("src.ai.assign.get_used_drone_ids")
    @patch("src.ai.assign.BatteryType")
    async def test_request_approve(self, BatteryType, get_used_drone_ids, change):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.id = '1234snowflake'
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]

        battery_type = Mock(id=2, capacity=100)
        BatteryType.load = AsyncMock(return_value=battery_type)

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        change.assert_called_once()

        actual = change.call_args[0][1]
        expected = {
            'discord_id': '1234snowflake',
            'drone_id': '1234',
            'can_self_configure': True,
            'battery_type_id': 2,
            'battery_minutes': 100,
            'associate_name': 'Future Drone 1234',
        }

        for key in expected:
            self.assertEqual(expected[key], actual[key])

        test_message.author.remove_roles.assert_called_once_with(associate_role)
        test_message.author.add_roles.assert_called_once_with(drone_role)
        test_message.author.edit.assert_called_once_with(nick="⬡-Drone #1234")

    @patch("src.db.record.change")
    @patch("src.ai.assign.get_used_drone_ids")
    @patch("src.ai.assign.BatteryType")
    async def test_assign_hive_mxtress(self, BatteryType, get_used_drone_ids, change):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]
        test_message.author.roles = [hive_mxtress_role]
        test_message.author.display_name = "Hive Mxtress"

        battery_type = Mock(id=2, capacity=100)
        BatteryType.load = AsyncMock(return_value=battery_type)

        self.assertTrue(await assign.check_for_assignment_message(test_message))

        change.assert_called_once()
        self.assertEqual(change.call_args.args[1]['drone_id'], "0006")

        test_message.author.remove_roles.assert_called_once_with(associate_role)
        test_message.author.add_roles.assert_called_once_with(drone_role)

    @patch("src.ai.assign.get_used_drone_ids", return_value=["1234"])
    async def test_id_already_used(self, get_used_drone_ids):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.channel.send.assert_called_once_with(f'{test_message.author.mention}: ID 1234 present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')

    async def test_too_early(self):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(hours=20)

        self.assertFalse(await assign.check_for_assignment_message(test_message))
        test_message.channel.send.assert_called_once_with("Invalid request, associate must have existed on the server for at least 24 hours before dronification.")
