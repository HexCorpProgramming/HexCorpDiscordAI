import unittest
from unittest.mock import AsyncMock, patch

import ai.assign as assign
from channels import ASSIGNMENT_CHANNEL

test_message = AsyncMock()


class AssignmentTest5(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        test_message.reset_mock()
        test_message.content = assign.ASSIGNMENT_MESSAGE
        test_message.channel.name = ASSIGNMENT_CHANNEL
        test_message.author.display_name = "Future Drone 1234"
        test_message.author.mention = "<mention_placeholder>"

    async def test_request_reject(self):
        test_message.content = "Beep Boop want to be drone!"

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_called_once()

    async def test_wrong_channel(self):
        test_message.channel.name = "some other channel"

        self.assertFalse(await assign.check_for_assignment_message(test_message))
        test_message.delete.assert_not_called()

    @patch("ai.assign.insert_drone")
    async def test_request_approve(self, insert_drone):
        self.assertTrue(await assign.check_for_assignment_message(test_message))
        self.assertEqual(insert_drone.called, 1)
        self.assertEqual(insert_drone.call_args.args[0].drone_id, "1234")

    @patch("ai.assign.get_used_drone_ids")
    async def test_id_already_used(self, get_used_drone_ids):
        get_used_drone_ids.return_value = ["1234"]

        self.assertTrue(await assign.check_for_assignment_message(test_message))
        test_message.channel.send.assert_called_once_with(f'{test_message.author.mention}: ID 1234 present in current nickname is already assigned to a drone. Please choose a different ID or contact Hive Mxtress.')
