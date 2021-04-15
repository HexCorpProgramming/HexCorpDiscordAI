import unittest
from unittest.mock import AsyncMock, patch, Mock
import ai.battery as battery


class TestBattery(unittest.IsolatedAsyncioTestCase):

    @patch("ai.battery.deincrement_battery_minutes_remaining")
    async def test_track_active_battery_drain(self, deincrement):
        '''
        For every inactive drone, 1 minute of battery should be drained from them
        via database call 'deincrement_battery_minutes_remaining'.
        Their 'active minutes remaining' should also be deincremented by one.
        '''

        bot = AsyncMock()

        battery_cog = battery.BatteryCog(bot)

        battery_cog.draining_batteries = {'5890': 10}

        battery_cog.track_active_battery_drain.start()
        battery_cog.track_active_battery_drain.stop()
        await battery_cog.track_active_battery_drain.get_task()

        deincrement.assert_called_once()
        self.assertEqual(battery_cog.draining_batteries.get('5890', None), 9)
