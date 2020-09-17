import unittest
from unittest.mock import AsyncMock, patch, Mock

import roles
import ai.assign as assign
from channels import ASSIGNMENT_CHANNEL

test_message = AsyncMock()

associate_role = Mock()
associate_role.name = roles.ASSOCIATE
drone_role = Mock()
drone_role.name = roles.DRONE


class AssignmentTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        test_message.reset_mock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"
        test_message.guild.roles = [associate_role, drone_role]

    async def test_request_reject(self):
        test_message.content = "Beep Boop want to be drone!"

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_called_once()

    async def test_wrong_channel(self):
        test_message.channel.name = "some other channel"

        self.assertFalse(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_not_called()

    @patch("ai.assign.insert_drone")
    @patch("ai.assign.get_used_drone_ids")
    async def test_request_approve(self, get_used_drone_ids, insert_drone):
        self.assertTrue(await assign.check_for_assignment_message(test_message))
        insert_drone.assert_called_once()
        self.assertEqual(insert_drone.call_args.args[0].drone_id, "1234")
        test_message.author.remove_roles.assert_called_once_with(associate_role)
        test_message.author.add_roles.assert_called_once_with(drone_role)
        test_message.author.edit.assert_called_once_with(nick="⬡-Drone #1234")

    @patch("ai.assign.get_used_drone_ids", return_value=["1234"])
    async def test_id_already_used(self, get_used_drone_ids):
        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.channel.send.assert_called_once_with(f'{test_message.author.mention}: ID 1234 present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
