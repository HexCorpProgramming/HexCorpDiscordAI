import unittest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import src.ai.mantra as mantra
from src.db.data_objects import BatteryType
from test.mocks import Mocks

mocks = Mocks()


class TestMantra(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        mantra.mantra_counters = {}

    @patch('src.ai.mantra.DroneMember')
    async def test_check_for_mantra(self, DroneMember: MagicMock):
        author = mocks.drone_member('1234', drone_is_battery_powered=True)
        DroneMember.create = AsyncMock(return_value=author)
        message = mocks.message(author, 'hive-repetitions', '1234 :: 301')

        await mantra.check_for_mantra(message)

        # assert
        self.assertEqual(len(mantra.mantra_counters.values()), 1)

    @patch('src.ai.mantra.DroneMember')
    async def check_not_handled(self, channel: str, is_battery_powered: bool, msg: str, DroneMember: MagicMock) -> None:
        author = mocks.drone_member('1234', drone_is_battery_powered=is_battery_powered)
        DroneMember.create = AsyncMock(return_value=author)
        message = mocks.message(author, 'hive-repetitions', '1234 :: ' + msg)

        await mantra.check_for_mantra(message)

        # assert
        self.assertEqual(len(mantra.mantra_counters.values()), 0)

    async def test_check_for_mantra_no_battery(self) -> None:
        await self.check_not_handled('hive-repetitions', False, '301')

    async def test_check_for_mantra_wrong_message(self) -> None:
        await self.check_not_handled('hive-repetitions', False, 'beep')

    async def test_check_for_mantra_wrong_channel(self) -> None:
        await self.check_not_handled('drone-configuration', False, '301')

    @patch('src.ai.mantra.increase_battery_by_five_percent')
    @patch.dict('src.ai.mantra.mantra_counters', {})
    async def test_increment_counter(self, increase_battery_by_five_percent: AsyncMock):
        author = mocks.drone_member('1234', drone_is_battery_powered=True)
        message = mocks.message(author, 'hive-repetitions')
        drone_id = '1234'

        code_match = Mock()
        code_match.group.return_value = '301'

        # run
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = '302'
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 2)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = '303'
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 3)
        increase_battery_by_five_percent.assert_not_called()

        # run
        code_match.group.return_value = '304'
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 0)
        increase_battery_by_five_percent.assert_called_once()
        increase_battery_by_five_percent.reset_mock()

        # run
        # loop around to 1 again
        code_match.group.return_value = '301'
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

        # run
        # do not advance if wrong order
        code_match.group.return_value = '303'
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertEqual(mantra.mantra_counters[drone_id], 1)
        increase_battery_by_five_percent.assert_not_called()

    @patch('src.ai.mantra.increase_battery_by_five_percent')
    @patch.dict('src.ai.mantra.mantra_counters', {})
    async def test_increment_counter_skipped_first(self, increase_battery_by_five_percent):
        # init
        author = mocks.drone_member('1234')
        message = mocks.message(author, 'hive-repetitions')
        drone_id = '1234'

        code_match = Mock()
        code_match.group.return_value = '302'

        # run
        await mantra.handle_mantra(author, message, code_match)

        # assert
        self.assertFalse(mantra.mantra_counters[drone_id], 0)
        increase_battery_by_five_percent.assert_not_called()

    async def increase_battery(self, minutes: int) -> None:
        # init
        author = mocks.drone_member('1234', drone_battery_minutes=minutes)
        message = mocks.message(author, 'hive-repetitions')
        message.channel.reset_mock()

        # run
        await mantra.increase_battery_by_five_percent(author, message)

        return author, message

    async def test_increase_battery_by_five_percent(self) -> None:
        author, message = await self.increase_battery(240)

        # assert
        self.assertEqual(author.drone.battery_minutes, 264)
        author.drone.save.assert_called_once()
        message.channel.send.assert_called_once_with('Good drone. Battery has been recharged by 5%.')

    async def test_increase_battery_by_five_percent_capped(self) -> None:
        author, message = await self.increase_battery(479)

        # assert
        self.assertEqual(author.drone.battery_minutes, 480)
        author.drone.save.assert_called_once()
        message.channel.send.assert_called_once_with('Good drone. Battery has been recharged by 5%.')

    async def test_increase_battery_by_five_percent_full(self) -> None:
        author, message = await self.increase_battery(480)

        # assert
        self.assertEqual(author.drone.battery_minutes, 480)
        author.drone.save.assert_not_called()
        message.channel.send.assert_called_once_with('Good drone. Battery already at 100%.')
