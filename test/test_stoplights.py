import unittest
from unittest.mock import AsyncMock, patch
from ai.stoplights import check_for_stoplights


class StoplightsTest(unittest.IsolatedAsyncioTestCase):

    mocked_mod_role = AsyncMock()
    mocked_mod_role.mention = "<!@666666>"

    @patch("ai.stoplights.get", return_value=mocked_mod_role)
    async def test_alert_mods_and_return_true_if_clock_in_message(self, mocked_get):

        clock_message = AsyncMock()
        clock_message.content = "I need help. ⏰"

        self.assertTrue(await check_for_stoplights(clock_message))
        clock_message.channel.send.assert_called_once_with(f"Moderators needed {StoplightsTest.mocked_mod_role.mention}!")

    async def test_return_true_if_stoplight_in_message(self):

        green_stoplight_message = AsyncMock()
        green_stoplight_message.content = "This is good!! Please carry on. 🟢🟢🟢"

        yellow_stoplight_message = AsyncMock()
        yellow_stoplight_message.content = "🟡 Mmmm, could you try something else?"

        red_stoplight_message = AsyncMock()
        red_stoplight_message.content = "🔴 This is making me uncomfortable."

        self.assertTrue(await check_for_stoplights(green_stoplight_message))
        self.assertTrue(await check_for_stoplights(yellow_stoplight_message))
        self.assertTrue(await check_for_stoplights(red_stoplight_message))

    async def test_return_false_if_no_stoplight_or_clock_in_message(self):

        benign_message = AsyncMock()
        benign_message.content = "9813 :: It feels good to obey. Beep boop."

        self.assertFalse(await check_for_stoplights(benign_message))
