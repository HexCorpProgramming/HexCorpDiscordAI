import unittest
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
from datetime import datetime, timedelta

import src.roles as roles
from src.ai.timers import TimersCog
from src.db.data_objects import Timer
import test.test_utils as test_utils


class TimersTest(unittest.IsolatedAsyncioTestCase):

    @patch("src.ai.timers.set_can_self_configure")
    @patch("src.ai.timers.update_display_name")
    @patch("src.ai.timers.convert_id_to_member")
    @patch("src.ai.timers.update_droneOS_parameter")
    @patch("src.ai.timers.fetch_drone_with_drone_id")
    @patch("src.ai.timers.delete_timer")
    @patch("src.ai.timers.get_timers_elapsed_before")
    async def test_process_timers(self,
                                  get_timers_elapsed_before,
                                  delete_timer,
                                  fetch_drone_with_drone_id,
                                  update_droneOS_parameter,
                                  convert_id_to_member,
                                  update_display_name,
                                  set_can_self_configure):
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
        await test_utils.start_and_await_loop(timer_cog.process_timers)

        # assert
        convert_id_to_member.assert_called_once_with(bot.guilds[0], timer.drone_id)
        drone_member.remove_roles.assert_called_once_with(optimized_role)
        delete_timer.assert_called_once_with(timer_id)
        update_display_name.assert_called_once_with(drone_member)
        set_can_self_configure.assert_called_once_with(drone_member)

    @patch("src.ai.timers.set_can_self_configure")
    @patch("src.ai.timers.update_display_name")
    @patch("src.ai.timers.convert_id_to_member")
    @patch("src.ai.timers.update_droneOS_parameter")
    @patch("src.ai.timers.fetch_drone_with_drone_id")
    @patch("src.ai.timers.delete_timer")
    @patch("src.ai.timers.get_timers_elapsed_before")
    async def test_process_timers_battery(self,
                                          get_timers_elapsed_before,
                                          delete_timer,
                                          fetch_drone_with_drone_id,
                                          update_droneOS_parameter,
                                          convert_id_to_member,
                                          update_display_name,
                                          set_can_self_configure):
        # setup
        battery_powered_role = Mock()
        battery_powered_role.name = roles.BATTERY_POWERED

        drone_member = AsyncMock()

        drone = Mock()
        drone.drone_id = '1865'

        bot = AsyncMock()
        bot.guilds[0].roles = [battery_powered_role]

        timer_cog = TimersCog(bot)

        timer_id = str(uuid4())
        timer = Timer(timer_id, drone.drone_id, 'is_battery_powered', datetime.now() - timedelta(minutes=2))

        get_timers_elapsed_before.return_value = [timer]
        convert_id_to_member.return_value = drone_member
        fetch_drone_with_drone_id.return_value = drone

        # run
        await test_utils.start_and_await_loop(timer_cog.process_timers)

        # assert
        convert_id_to_member.assert_called_once_with(bot.guilds[0], timer.drone_id)
        drone_member.remove_roles.assert_called_once_with(battery_powered_role)
        delete_timer.assert_called_once_with(timer_id)
        update_display_name.assert_called_once_with(drone_member)
        set_can_self_configure.assert_called_once_with(drone_member)
