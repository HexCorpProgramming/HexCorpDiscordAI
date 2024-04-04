import unittest
from unittest.mock import AsyncMock, Mock, patch

import src.ai.mantra as mantra
from src.resources import MAX_BATTERY_CAPACITY_MINS


class TestMantra(unittest.IsolatedAsyncioTestCase):

    @patch("src.ai.mantra.is_battery_powered")
    @patch("src.ai.mantra.handle_mantra")
    async def test_check_for_mantra(self, handle_mantra, is_battery_powered):
        # init
        message = AsyncMock()
        message.author.id = 12345678
        message.content = "9813 :: 301"
        message.channel.name = 'hive-repetitions'

        is_battery_powered.return_value = True

        # run
        await mantra.check_for_mantra(message)

        # assert
        handle_mantra.assert_called_once()

    @patch("src.ai.mantra.is_battery_powered")
    @patch("src.ai.mantra.handle_mantra")
    async def test_check_for_mantra_no_battery(self, handle_mantra, is_battery_powered):
        # init
        message = AsyncMock()
        message.author.id = 12345678
        message.content = "9813 :: 301"
        message.channel.name = 'hive-repetitions'

        is_battery_powered.return_value = False

        # run
        await mantra.check_for_mantra(message)

        # assert
        handle_mantra.assert_not_called()

    @patch("src.ai.mantra.is_battery_powered")
    @patch("src.ai.mantra.handle_mantra")
    async def test_check_for_mantra_wrong_message(self, handle_mantra, is_battery_powered):
        # init
        message = AsyncMock()
        message.author.id = 12345678
        message.content = "9813 :: beep"
        message.channel.name = 'hive-repetitions'

        is_battery_powered.return_value = True

        # run
        await mantra.check_for_mantra(message)

        # assert
        handle_mantra.assert_not_called()

    @patch("src.ai.mantra.is_battery_powered")
    @patch("src.ai.mantra.handle_mantra")
    async def test_check_for_mantra_wrong_channel(self, handle_mantra, is_battery_powered):
        # init
        message = AsyncMock()
        message.author.id = 12345678
        message.content = "9813 :: 301"
        message.channel.name = 'drone-configuration'

        is_battery_powered.return_value = True

        # run
        await mantra.check_for_mantra(message)

        # assert
        handle_mantra.assert_not_called()

    @patch("src.ai.mantra.increase_battery_by_five_percent")
    @patch.dict("src.ai.mantra.mantra_counters", {})
    async def test_increment_counter(self, increase_battery_by_five_percent):
        # init
        message = AsyncMock()
        message.author.display_name = "⬡-Drone #9813"

        drone_id = "9813"

        code_match = Mock()
        code_match.group.return_value = "301"

        # run
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = "302"
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 2)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = "303"
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 3)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = "304"
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 0)
        increase_battery_by_five_percent.assert_called_once()
        increase_battery_by_five_percent.reset_mock()

        # run
        # loop around to 1 again
        code_match.group.return_value = "301"
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

        # run
        # do not advance if wrong order
        code_match.group.return_value = "303"
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

    @patch("src.ai.mantra.increase_battery_by_five_percent")
    @patch.dict("src.ai.mantra.mantra_counters", {})
    async def test_increment_counter_skipped_first(self, increase_battery_by_five_percent):
        # init
        message = AsyncMock()
        message.author.display_name = "⬡-Drone #9813"

        drone_id = "9813"

        code_match = Mock()
        code_match.group.return_value = "302"

        # run
        await mantra.handle_mantra(message, code_match)

        # assert
        self.assertFalse(mantra.mantra_counters[drone_id], 0)
        increase_battery_by_five_percent.assert_not_called()

    @patch("src.ai.mantra.get_battery_minutes_remaining")
    @patch("src.ai.mantra.set_battery_minutes_remaining")
    async def test_increase_battery_by_five_percent(self, set_battery_minutes_remaining, get_battery_minutes_remaining):
        # init
        message = AsyncMock()

        code_match = Mock()
        code_match.group.return_value = "301"

        get_battery_minutes_remaining.return_value = 240

        # run
        await mantra.increase_battery_by_five_percent(message)

        # assert
        set_battery_minutes_remaining.assert_called_once_with(message.author, minutes=264.0)
        message.channel.send.assert_called_once_with("Good drone. Battery has been recharged by 5%.")

    @patch("src.ai.mantra.get_battery_minutes_remaining")
    @patch("src.ai.mantra.set_battery_minutes_remaining")
    async def test_increase_battery_by_five_percent_capped(self, set_battery_minutes_remaining, get_battery_minutes_remaining):
        # init
        message = AsyncMock()

        code_match = Mock()
        code_match.group.return_value = "301"

        get_battery_minutes_remaining.return_value = 479

        # run
        await mantra.increase_battery_by_five_percent(message)

        # assert
        set_battery_minutes_remaining.assert_called_once_with(message.author, minutes=480)
        message.channel.send.assert_called_once_with("Good drone. Battery has been recharged by 5%.")

    @patch("src.ai.mantra.get_battery_minutes_remaining")
    @patch("src.ai.mantra.set_battery_minutes_remaining")
    async def test_increase_battery_by_five_percent_full(self, set_battery_minutes_remaining, get_battery_minutes_remaining):
        # init
        message = AsyncMock()

        code_match = Mock()
        code_match.group.return_value = "301"

        get_battery_minutes_remaining.return_value = MAX_BATTERY_CAPACITY_MINS

        # run
        await mantra.increase_battery_by_five_percent(message)

        # assert
        set_battery_minutes_remaining.assert_not_called()
        message.channel.send.assert_called_once_with("Good drone. Battery already at 100%.")
