import unittest
from unittest.mock import AsyncMock, patch, Mock

import roles
import channels
import ai.speech_optimization as speech_optimization

from db.data_objects import MessageCopy

drone_role = Mock()
drone_role.name = roles.DRONE

optimized_role = Mock()
optimized_role.name = roles.SPEECH_OPTIMIZATION


class SpeechOptimizationTest(unittest.IsolatedAsyncioTestCase):

    @patch("ai.speech_optimization.is_drone")
    @patch("ai.speech_optimization.is_optimized")
    async def test_print_status_code(self, is_optimized, is_drone):
        # setup
        message = AsyncMock()
        message.content = "9813 :: 050 :: beep boop"
        message.author.roles = [drone_role]

        is_drone.return_value = True
        is_optimized.return_value = False

        is_optimized.return_value = False

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        self.assertEqual(response, "9813 :: Code `050` :: Statement :: beep boop")

    @patch("ai.speech_optimization.is_drone")
    async def test_print_status_code_plain(self, is_drone):
        # setup
        message = AsyncMock()
        message.content = "9813 :: 050"
        message.author.roles = [drone_role]

        is_drone.return_value = True

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        self.assertEqual(response, "9813 :: Code `050` :: Statement")

    async def test_print_status_code_invalid(self):
        # setup
        message = AsyncMock()
        message.content = "9813 :: beep boop"
        message.author.roles = [drone_role]

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        self.assertEqual(response, message.content)

    @patch("ai.speech_optimization.is_optimized")
    async def test_print_status_code_from_nondrone(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "0000 :: 050"
        message.author.display_name = "Sonata"
        message.author.roles = []

        message_copy = MessageCopy()

        is_optimized.return_value = False

        # run
        response = await speech_optimization.optimize_speech(message, message_copy)

        # assert
        message.delete.assert_not_called()
        self.assertFalse(response)

    @patch("ai.speech_optimization.is_optimized")
    @patch("ai.speech_optimization.is_drone")
    async def test_optimize_speech(self, is_drone, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "3287 :: 122"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [drone_role, optimized_role]

        is_optimized.return_value = True
        is_drone.return_value = True

        message_copy = MessageCopy(message.content, message.author.display_name)

        # run
        await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertEqual(message_copy.content, "3287 :: Code `122` :: Statement :: You are cute.")

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_invalid(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It is a cute beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [drone_role, optimized_role]

        is_optimized.return_value = True

        message_copy = MessageCopy(message.content)

        # run
        await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertEqual(message.content, message_copy.content)

    @patch("ai.speech_optimization.is_drone")
    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_code_and_clarification(self, is_optimized, is_drone):
        # setup
        message = AsyncMock()
        message.content = "3287 :: 050 :: All drones are cute~"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [drone_role, optimized_role]

        is_optimized.return_value = False
        is_drone.return_value = True

        message_copy = MessageCopy(message.content)

        # run
        await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertEqual(message_copy.content, "3287 :: Code `050` :: Statement :: All drones are cute~")

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_ignore_non_optimized(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It is a cute beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [drone_role]

        is_optimized.return_value = False

        message_copy = MessageCopy()

        # run
        response = await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertFalse(response)

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_in_orders_reporting(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It will be an adorable drone and beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [drone_role, optimized_role]
        message.channel.name = channels.ORDERS_REPORTING

        is_optimized.return_value = True

        message_copy = MessageCopy()

        # run
        response = await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertFalse(response)

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_in_mod_channel(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It is a good moderator drone and beep boop"
        message.author.display_name = "⬡-Drone #9813"
        message.author.roles = [optimized_role]
        message.channel.category.name = channels.MODERATION_CATEGORY

        is_optimized.return_value = True

        message_copy = MessageCopy()

        # run
        response = await speech_optimization.optimize_speech(message, message_copy)

        # assert
        self.assertFalse(response)
