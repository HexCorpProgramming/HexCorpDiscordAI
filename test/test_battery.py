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

    async def test_remove_from_active_tracking(self):
        '''
        If an inactive drone has 0 minutes of draining left, they should be
        removed from the dictionary.
        '''

        bot = AsyncMock()

        battery_cog = battery.BatteryCog(bot)

        battery_cog.draining_batteries = {'9813': 0}

        battery_cog.track_active_battery_drain.start()
        battery_cog.track_active_battery_drain.stop()
        await battery_cog.track_active_battery_drain.get_task()

        self.assertIsNone(battery_cog.draining_batteries.get('9813', None))

    @patch("ai.battery.has_role", return_value=True)
    @patch("ai.battery.get")
    @patch("ai.battery.get_all_drone_batteries")
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

        drone_5890 = Mock()
        drone_5890.id = "some_discord_id"
        drone_5890.battery_minutes = 0
        drone_batteries.return_value = [drone_5890]

        battery_cog = battery.BatteryCog(bot)

        battery_cog.track_drained_batteries.start()
        battery_cog.track_drained_batteries.stop()
        await battery_cog.track_drained_batteries.get_task()

        member.add_roles.assert_called_once_with(drained_role)

    @patch("ai.battery.has_role", return_value=True)
    @patch("ai.battery.get")
    @patch("ai.battery.get_all_drone_batteries")
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

        battery_cog.track_drained_batteries.start()
        battery_cog.track_drained_batteries.stop()
        await battery_cog.track_drained_batteries.get_task()

        member.remove_roles.assert_called_once_with(drained_role)

    @patch("ai.battery.get_all_drone_batteries")
    async def test_warn_low_battery_drones(self, drone_batteries):
        '''
        The AI Mxtress should warn drones with less than 30 percent battery
        by DMing them.
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

        battery_cog.warn_low_battery_drones.start()
        battery_cog.warn_low_battery_drones.stop()
        await battery_cog.warn_low_battery_drones.get_task()
        
        member.send.assert_called_once_with("Attention. Your battery is low (30%). Please connect to main power grid in the Storage Facility immediately.")
        self.assertTrue('5890' in battery_cog.low_battery_drones)

    @patch("ai.battery.get_all_drone_batteries")
    async def test_drone_not_warned_more_than_one(self, drone_batteries):
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

        battery_cog.warn_low_battery_drones.start()
        battery_cog.warn_low_battery_drones.stop()
        await battery_cog.warn_low_battery_drones.get_task()
    
        member.send.assert_not_called()

    @patch("ai.battery.get_all_drone_batteries")
    async def test_remove_recharged_drones(self, drone_batteries):
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

        battery_cog.warn_low_battery_drones.start()
        battery_cog.warn_low_battery_drones.stop()
        await battery_cog.warn_low_battery_drones.get_task()
    
        member.send.assert_not_called()
        self.assertTrue('5890' not in battery_cog.low_battery_drones)

    @patch("ai.battery.get")
    @patch("ai.battery.get_battery_percent_remaining")
    @patch("ai.battery.is_battery_powered", return_value=True)
    async def test_append_battery_indicator(self, battery_powered, battery_percentage, discord_get):
        
        message = Mock()
        message_copy = Mock()
        original_message = "Hello."

        battery_high = Mock()
        battery_mid = Mock()
        battery_low = Mock()
        battery_empty = Mock()

        discord_get.side_effect = [battery_high, battery_mid, battery_low, battery_empty]

        bot = Mock()
        battery_cog = battery.BatteryCog(bot)

        battery_percentage.return_value = 100
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"{str(battery_high)} :: {original_message}")

        battery_percentage.return_value = 50
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"{str(battery_mid)} :: {original_message}")

        battery_percentage.return_value = 20
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"{str(battery_low)} :: {original_message}")

        battery_percentage.return_value = 5
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"{str(battery_empty)} :: {original_message}")


    @patch("ai.battery.get")
    @patch("ai.battery.get_battery_percent_remaining", return_value=100)
    @patch("ai.battery.is_battery_powered", return_value=True)
    async def test_append_battery_indicator_with_prepending(self, battery_powered, battery_percentage, discord_get):
        
        message = Mock()
        message_copy = Mock()
        original_message = "5890 :: Hello."

        battery_high = Mock()
        battery_mid = Mock()
        battery_low = Mock()
        battery_empty = Mock()

        discord_get.side_effect = [battery_high, battery_mid, battery_low, battery_empty]

        bot = Mock()
        battery_cog = battery.BatteryCog(bot)

        battery_percentage.return_value = 100
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"5890 :: {str(battery_high)} :: Hello.")

        battery_percentage.return_value = 50
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"5890 :: {str(battery_mid)} :: Hello.")

        battery_percentage.return_value = 20
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"5890 :: {str(battery_low)} :: Hello.")

        battery_percentage.return_value = 5
        message_copy.content = original_message
        await battery_cog.append_battery_indicator(message, message_copy)
        self.assertEqual(message_copy.content, f"5890 :: {str(battery_empty)} :: Hello.")