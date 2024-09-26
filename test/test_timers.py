import unittest
from unittest.mock import AsyncMock, patch
import src.roles as roles
from src.ai.timers import TimersCog
from test.test_utils import start_and_await_loop
from test.mocks import Mocks
from test.cog import cog


class TimersTest(unittest.IsolatedAsyncioTestCase):

    @patch('src.ai.timers.Timer', new_callable=AsyncMock)
    @cog(TimersCog)
    async def test_process_timers(self, Timer: AsyncMock, mocks: Mocks) -> None:
        '''
        A drone with a configuration option enabled should have it disabled when the timer expires.
        '''

        tests = [
            ('optimized', roles.SPEECH_OPTIMIZATION),
            ('is_battery_powered', roles.BATTERY_POWERED),
        ]

        for (mode, role) in tests:
            member = mocks.drone_member('1234', roles=[role])
            setattr(member.drone, mode, True)
            member.drone.timer = mocks.timer(mode=mode)
            Timer.all_elapsed.return_value = [member]

            await start_and_await_loop(mocks.get_cog().process_timers)

            self.assertFalse(getattr(member.drone, mode))
            member.remove_roles.assert_called_once_with(mocks.role(role))
            self.assertTrue(member.drone.can_self_configure)
            member.drone.save.assert_called_once()
