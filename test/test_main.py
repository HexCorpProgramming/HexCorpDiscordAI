import unittest
from unittest.mock import AsyncMock, patch

import main
import channels


class MainTest(unittest.IsolatedAsyncioTestCase):

    @patch("main.emote")
    async def test_bigtext(self, emote):
        # setup
        context = AsyncMock()
        context.channel.name = channels.TRANSMISSIONS_CHANNEL

        # run
        await main.bigtext(context, "beep boop")

        # assert
        emote.generate_big_text.assert_called_once_with(context.channel, "beep boop")
