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

    @patch("src.ai.assign.insert_drone")
    @patch("src.ai.assign.get_used_drone_ids")
    async def test_request_approve(self, get_used_drone_ids, insert_drone):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        insert_drone.assert_called_once()
        self.assertEqual(insert_drone.call_args.args[0].drone_id, "1234")
        self.assertEqual(insert_drone.call_args.args[0].associate_name, "Future Drone 1234")
        test_message.author.remove_roles.assert_called_once_with(associate_role)
        test_message.author.add_roles.assert_called_once_with(drone_role)
        test_message.author.edit.assert_called_once_with(nick="⬡-Drone #1234")

    @patch("src.ai.assign.insert_drone")
    @patch("src.ai.assign.get_used_drone_ids")
    async def test_assign_hive_mxtress(self, get_used_drone_ids, insert_drone):
        test_message = AsyncMock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.author.joined_at = datetime.now(timezone.utc) - timedelta(weeks=2)
        test_message.guild.roles = [associate_role, drone_role, hive_mxtress_role]
        test_message.author.roles = [hive_mxtress_role]
        test_message.author.display_name = "Hive Mxtress"

        self.assertTrue(await assign.check_for_assignment_message(test_message))

        insert_drone.assert_called_once()
        self.assertEqual(insert_drone.call_args.args[0].drone_id, "0006")

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
