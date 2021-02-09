import unittest
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
from datetime import datetime, timedelta

import roles
from ai.timers import TimersCog
from db.data_objects import Timer


class TimersTest(unittest.IsolatedAsyncioTestCase):

    @patch("ai.timers.update_display_name")
    @patch("ai.timers.convert_id_to_member")
    @patch("ai.timers.update_droneOS_parameter")
    @patch("ai.timers.fetch_drone_with_drone_id")
    @patch("ai.timers.delete_timer")
    @patch("ai.timers.get_timers_elapsed_before")
    async def test_process_timers(self,
                                  get_timers_elapsed_before,
                                  delete_timer,
                                  fetch_drone_with_drone_id,
                                  update_droneOS_parameter,
                                  convert_id_to_member,
                                  update_display_name):
        # setup
        optimized_role = Mock()
        optimized_role.name = roles.SPEECH_OPTIMIZATION

        drone_member = AsyncMock()

        drone = Mock()
        drone.drone_id = '1865'

        bot = AsyncMock()
        bot.guilds[0].roles = [optimized_role]

        timer_cog = TimersCog(bot)

        timer_id = str(uuid4())
        timer = Timer(timer_id, drone.drone_id, 'optimized', datetime.now() - timedelta(minutes=2))

        get_timers_elapsed_before.return_value = [timer]
        convert_id_to_member.return_value = drone_member
        fetch_drone_with_drone_id.return_value = drone

        # run
        timer_cog.process_timers.start()
        timer_cog.process_timers.stop()
        await timer_cog.process_timers.get_task()

        # assert
        convert_id_to_member.assert_called_once_with(bot.guilds[0], timer.drone_id)
        drone_member.remove_roles.assert_called_once_with(optimized_role)
        delete_timer.assert_called_once_with(timer_id)
        update_display_name.assert_called_once_with(drone_member)
