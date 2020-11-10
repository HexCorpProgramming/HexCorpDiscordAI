import unittest
from unittest.mock import AsyncMock, patch, Mock

import roles
import channels
import ai.speech_optimization as speech_optimization

optimized_role = Mock()
optimized_role.name = roles.SPEECH_OPTIMIZATION


class SpeechOptimizationTest(unittest.IsolatedAsyncioTestCase):

    async def test_print_status_code(self):
        # setup
        message = AsyncMock()
        message.content = "9813 :: 050 :: beep boop"

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        message.delete.assert_called_once()
        self.assertEqual(response, "9813 :: Code `050` :: Statement :: beep boop")

    async def test_print_status_code_plain(self):
        # setup
        message = AsyncMock()
        message.content = "9813 :: 050"

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        message.delete.assert_called_once()
        self.assertEqual(response, "9813 :: Code `050` :: Statement")

    async def test_print_status_code_invalid(self):
        # setup
        message = AsyncMock()
        message.content = "9813 :: beep boop"

        # run
        response = await speech_optimization.print_status_code(message)

        # assert
        message.delete.assert_not_called()
        self.assertFalse(response)

    @patch("ai.speech_optimization.is_optimized")
    @patch("ai.speech_optimization.send_webhook_with_specific_output")
    @patch("ai.speech_optimization.get_webhook_for_channel")
    async def test_optimize_speech(self, get_webhook_for_channel, send_webhook_with_specific_output, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "3287 :: 122"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [optimized_role]

        is_optimized.return_value = True

        webhook = AsyncMock()
        get_webhook_for_channel.return_value = webhook

        # run
        await speech_optimization.optimize_speech(message)

        # assert
        message.delete.assert_called_once()
        get_webhook_for_channel.assert_called_once_with(message.channel)
        send_webhook_with_specific_output.assert_called_once_with(message.channel, message.author, webhook, "3287 :: Code `122` :: Statement :: You are cute.")

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_invalid(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It is a cute beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [optimized_role]

        is_optimized.return_value = True

        # run
        await speech_optimization.optimize_speech(message)

        # assert
        message.delete.assert_called_once()

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_code_and_clarification(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "3287 :: 050 :: All drones are cute~"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [optimized_role]

        is_optimized.return_value = True

        # run
        await speech_optimization.optimize_speech(message)

        # assert
        message.delete.assert_called_once()

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_ignore_non_optimized(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It is a cute beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = []

        is_optimized.return_value = False

        # run
        await speech_optimization.optimize_speech(message)

        # assert
        message.delete.assert_not_called()

    @patch("ai.speech_optimization.is_optimized")
    async def test_optimize_speech_in_orders_reporting(self, is_optimized):
        # setup
        message = AsyncMock()
        message.content = "It will be an adorable drone and beep boop"
        message.author.display_name = "⬡-Drone #3287"
        message.author.roles = [optimized_role]
        message.channel.name = channels.ORDERS_REPORTING

        is_optimized.return_value = True

        # run
        await speech_optimization.optimize_speech(message)

        # assert
        message.delete.assert_not_called()
