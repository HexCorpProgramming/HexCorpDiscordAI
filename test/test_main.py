import unittest
from unittest.mock import AsyncMock, patch, ANY

import main


class MainTest(unittest.IsolatedAsyncioTestCase):

    @patch("main.bot_message_listeners")
    @patch("main.message_listeners")
    async def test_on_message(self, message_listeners, bot_message_listeners):
        # init
        first_listener = AsyncMock(return_value=False)
        second_listener = AsyncMock(return_value=False)
        third_listener = AsyncMock(return_value=True)
        fourth_listener = AsyncMock(return_value=False)

        message_listeners.__iter__.return_value = iter([first_listener, second_listener, third_listener, fourth_listener])
        bot_message_listeners.__iter__.return_value = iter([])

        message = AsyncMock()
        message.content = "beep boop"
        message.author.bot = False

        # run
        await main.on_message(message)

        # assert
        first_listener.assert_any_call(message, ANY)
        second_listener.assert_any_call(message, ANY)
        third_listener.assert_any_call(message, ANY)
        fourth_listener.assert_not_called()
