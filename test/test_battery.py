import unittest
from unittest.mock import AsyncMock, patch, Mock
import src.ai.battery as battery
import src.emoji as emoji
import test.test_utils as test_utils
from src.db.drone_dao import BatteryType, Drone


class TestBattery(unittest.IsolatedAsyncioTestCase):

    @patch("src.ai.battery.get_battery_minutes_remaining", return_value=20)
    @patch("src.ai.battery.set_battery_minutes_remaining")
    @patch("src.ai.battery.get_battery_type", return_value=BatteryType(2, 'High', 480, 240))
    async def test_recharge_battery(self, get_battery_type, set_bat_mins, get_bat_mins):
        '''
        The recharge battery function should call the
        set_battery_minutes_remaining() function with an accurate amount
        of minutes of recharge (4 hours of charge for every hour in storage)
        '''

        member = Mock()
        member.id = '5890snowflake'

        await battery.recharge_battery(member.id)

        set_bat_mins.assert_called_once_with(member.id, 20 + 240)

    @patch("src.ai.battery.get_battery_minutes_remaining", return_value=320)
    @patch("src.ai.battery.set_battery_minutes_remaining")
    @patch("src.ai.battery.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_manually_drain_battery(self, get_battery_type, set_bat_mins, get_bat_mins):
        '''
        The recharge battery function should call the
        set_battery_minutes_remaining() function with an accurate amount
        of minutes of recharge (4 hours of charge for every hour in storage)
        '''

        member = AsyncMock()
        member.display_name = "⬢-Drone #3287"

        await battery.drain_battery(member)

        get_bat_mins.assert_called_once_with(member.id)
        set_bat_mins.assert_called_once_with(member.id, 320 - 480 / 10)

    @patch("src.ai.battery.get_battery_minutes_remaining", return_value=500)
    @patch("src.ai.battery.set_battery_minutes_remaining")
    @patch("src.ai.battery.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_recharge_battery_no_overcharge(self, get_battery_type, set_bat_mins, get_bat_mins):
        '''
        The recharge battery function should not call
        set_battery_minutes_remaining with more than the maximum capacity (480)
        '''

        member = Mock()
        member.id = '5890snowflake'

        await battery.recharge_battery(member.id)

        set_bat_mins.assert_called_once_with(member.id, 480)

    @patch("src.ai.battery.deincrement_battery_minutes_remaining")
    async def test_track_active_battery_drain(self, deincrement):
        '''
        For every inactive drone, 1 minute of battery should be drained from them
        via database call 'deincrement_battery_minutes_remaining'.
        Their 'active minutes remaining' should also be deincremented by one.
        '''

        bot = AsyncMock()

        battery_cog = battery.BatteryCog(bot)

        battery_cog.draining_batteries = {'5890': 10}

        await test_utils.start_and_await_loop(battery_cog.track_active_battery_drain)

        deincrement.assert_called_once()
        self.assertEqual(battery_cog.draining_batteries.get('5890', None), 9)

    async def test_remove_from_active_tracking(self):
        '''
        If an inactive drone has 0 minutes of draining left, they should be
        removed from the dictionary.
        '''

        bot = AsyncMock()

        battery_cog = battery.BatteryCog(bot)

        battery_cog.draining_batteries = {'9813': 0}

        await test_utils.start_and_await_loop(battery_cog.track_active_battery_drain)

        self.assertIsNone(battery_cog.draining_batteries.get('9813', None))

    @patch("src.ai.battery.has_role", return_value=True)
    @patch("src.ai.battery.get")
    @patch("src.ai.battery.get_all_drone_batteries")
    async def test_add_drained_role(self, drone_batteries, discord_get, has_role):
        '''
        Battery module should add the drained role if drone has 0 minutes
        of battery left.
        '''

        bot = AsyncMock()
        guild = Mock()
        member = AsyncMock()
        guild.get_member.return_value = member
        bot.guilds = [guild]

        drained_role = Mock()
        discord_get.return_value = drained_role

        drone_5890 = Drone('5890snowflake', '5890', battery_minutes=0)
        drone_batteries.return_value = [drone_5890]

        battery_cog = battery.BatteryCog(bot)

        await test_utils.start_and_await_loop(battery_cog.track_drained_batteries)

        member.add_roles.assert_called_once_with(drained_role)

    @patch("src.ai.battery.has_role", return_value=True)
    @patch("src.ai.battery.get")
    @patch("src.ai.battery.get_all_drone_batteries")
    async def test_remove_drained_role(self, drone_batteries, discord_get, has_role):
        '''
        Battery module should remove the drained role from drones that have it
        if they have more than 0 minutes of charge.
        '''

        bot = AsyncMock()
        guild = Mock()
        member = AsyncMock()
        guild.get_member.return_value = member
        bot.guilds = [guild]

        drained_role = Mock()
        discord_get.return_value = drained_role

        drone_5890 = Mock()
        drone_5890.id = "some_discord_id"
        drone_5890.battery_minutes = 200
        drone_batteries.return_value = [drone_5890]

        battery_cog = battery.BatteryCog(bot)

        await test_utils.start_and_await_loop(battery_cog.track_drained_batteries)

        member.remove_roles.assert_called_once_with(drained_role)

    @patch("src.ai.battery.get_all_drone_batteries")
    @patch("src.ai.battery.get_battery_percent_remaining", return_value=10)
    async def test_warn_low_battery_drones(self, get_battery_percent_remaining, drone_batteries):
        '''
        The AI Mxtress should warn drones with less than 30 percent battery
        by DMing them.
        '''

        drone = Drone('5890snowflake', '5890', battery_minutes=20)
        drone_batteries.return_value = [drone]

        bot = AsyncMock()
        guild = Mock()
        member = AsyncMock()
        guild.get_member.return_value = member
        bot.guilds = [guild]

        battery_cog = battery.BatteryCog(bot)

        await test_utils.start_and_await_loop(battery_cog.warn_low_battery_drones)

        member.send.assert_called_once_with("Attention. Your battery is low (30%). Please connect to main power grid in the Storage Facility immediately.")
        self.assertTrue('5890' in battery_cog.low_battery_drones)

    @patch("src.ai.battery.get_all_drone_batteries")
    @patch("src.ai.battery.get_battery_percent_remaining", return_value=30)
    async def test_drone_not_warned_more_than_one(self, get_battery_percent_remaining, drone_batteries):
        '''
        The AI Mxtress should only DM low battery drones once. If a drone
        has already been warned it should not be warned again until it is
        above 30% battery again.
        '''

        drone = Mock()
        drone.battery_minutes = 20
        drone.drone_id = '5890'
        drone_batteries.return_value = [drone]

        bot = AsyncMock()
        guild = Mock()
        member = AsyncMock()
        guild.get_member.return_value = member
        bot.guilds = [guild]

        battery_cog = battery.BatteryCog(bot)
        battery_cog.low_battery_drones = ['5890']

        await test_utils.start_and_await_loop(battery_cog.warn_low_battery_drones)

        member.send.assert_not_called()

    @patch("src.ai.battery.get_all_drone_batteries")
    @patch("src.ai.battery.get_battery_percent_remaining", return_value=50)
    async def test_remove_recharged_drones(self, get_battery_percent_remaining, drone_batteries):
        '''
        The AI Mxtress should remove drones from the list of warned drones
        once they are recharged above 30%.
        '''

        drone = Mock()
        drone.battery_minutes = 300
        drone.drone_id = '5890'
        drone_batteries.return_value = [drone]

        bot = AsyncMock()
        guild = Mock()
        member = AsyncMock()
        guild.get_member.return_value = member
        bot.guilds = [guild]

        battery_cog = battery.BatteryCog(bot)
        battery_cog.low_battery_drones = ['5890']

        await test_utils.start_and_await_loop(battery_cog.warn_low_battery_drones)

        member.send.assert_not_called()
        self.assertTrue('5890' not in battery_cog.low_battery_drones)

    def battery_emoji_getter(self, whatever, name):
        if name == emoji.BATTERY_FULL:
            return "FULLBATTERYEMOJI"
        elif name == emoji.BATTERY_MID:
            return "MIDBATTERYEMOJI"
        elif name == emoji.BATTERY_LOW:
            return "LOWBATTERYEMOJI"
        elif name == emoji.BATTERY_EMPTY:
            return "EMPTYBATTERYEMOJI"
        else:
            return "SHOULDNTHAPPEN"

    @patch("src.ai.battery.get")
    @patch("src.ai.battery.get_battery_percent_remaining")
    @patch("src.ai.battery.is_battery_powered", return_value=True)
    async def test_append_battery_indicator(self, battery_powered, battery_percentage, discord_get):
        '''
        When passed a message by a battery powered drone, should append
        a battery emoji to the start of their message ([++-]- :: Hello.)
        '''

        message = Mock()
        message_copy = Mock()
        original_message = "Hello."

        discord_get.side_effect = self.battery_emoji_getter

        battery_percentage.return_value = 100
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"FULLBATTERYEMOJI :: {original_message}")

        battery_percentage.return_value = 50
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"MIDBATTERYEMOJI :: {original_message}")

        battery_percentage.return_value = 20
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"LOWBATTERYEMOJI :: {original_message}")

        battery_percentage.return_value = 5
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"EMPTYBATTERYEMOJI :: {original_message}")

    @patch("src.ai.battery.get")
    @patch("src.ai.battery.get_battery_percent_remaining", return_value=100)
    @patch("src.ai.battery.is_battery_powered", return_value=True)
    async def test_append_battery_indicator_with_prepending(self, battery_powered, battery_percentage, discord_get):
        '''
        When passed a message by a battery powered drone, should append a
        battery indicator emoji after the drone ID and before the message
        content (5890 :: [++-]- :: Hello.)
        '''

        message = Mock()
        message_copy = Mock()
        original_message = "5890 :: Hello.\nBeep boop."

        discord_get.side_effect = self.battery_emoji_getter

        battery_percentage.return_value = 100
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, "5890 :: FULLBATTERYEMOJI :: Hello.\nBeep boop.")

        battery_percentage.return_value = 50
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, "5890 :: MIDBATTERYEMOJI :: Hello.\nBeep boop.")

        battery_percentage.return_value = 20
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, "5890 :: LOWBATTERYEMOJI :: Hello.\nBeep boop.")

        battery_percentage.return_value = 5
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, "5890 :: EMPTYBATTERYEMOJI :: Hello.\nBeep boop.")

    @patch("src.ai.battery.is_drone", return_value=True)
    @patch("src.ai.battery.is_battery_powered", return_value=True)
    async def test_start_battery_drain(self, bat_pow, is_drn):
        '''
        Battery powered drones should have their active tracking minutes
        set to 15 when they first send a message.
        '''

        message = Mock()
        message.author.display_name = "HexDrone 5890"

        message_copy = Mock()

        bot = Mock()
        battery_cog = battery.BatteryCog(bot)

        await battery_cog.start_battery_drain(message, message_copy)

        self.assertEqual(battery_cog.draining_batteries.get("5890", None), 15)

    @patch("src.ai.battery.is_drone", return_value=True)
    @patch("src.ai.battery.is_battery_powered", return_value=True)
    async def test_restart_battery_drain(self, bat_pow, is_drn):
        '''
        Drones that are currently being tracked for battery drain should have
        their minutes reset to 15 if they send another message.
        '''

        message = Mock()
        message.author.display_name = "HexDrone 5890"

        message_copy = Mock()

        bot = Mock()
        battery_cog = battery.BatteryCog(bot)

        battery_cog.draining_batteries['5890'] = 6

        await battery_cog.start_battery_drain(message, message_copy)

        self.assertEqual(battery_cog.draining_batteries.get("5890", None), 15)
