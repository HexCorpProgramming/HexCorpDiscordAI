import unittest
from unittest.mock import AsyncMock, Mock, patch
import src.ai.battery as battery
import src.emoji as emoji
import test.test_utils as test_utils
from src.roles import BATTERY_DRAINED, BATTERY_POWERED
from test.cog import cog
from test.mocks import Mocks


class TestBattery(unittest.IsolatedAsyncioTestCase):

    @cog(battery.BatteryCog)
    async def test_recharge_battery(self, mocks: Mocks):
        '''
        The recharge battery function should call the
        set_battery_minutes_remaining() function with an accurate amount
        of minutes of recharge (4 hours of charge for every hour in storage)
        '''

        drone = mocks.drone('1234')

        await battery.recharge_battery(drone)

        self.assertEqual(drone.battery_minutes, 220)
        drone.save.assert_called_once()

    @cog(battery.BatteryCog)
    async def test_manually_drain_battery(self, mocks: Mocks):
        '''
        The recharge battery function should call the
        set_battery_minutes_remaining() function with an accurate amount
        of minutes of recharge (4 hours of charge for every hour in storage)
        '''

        message = mocks.command(mocks.hive_mxtress(), 'general', 'drain 1234')
        drone_member = mocks.drone_member('1234', drone_is_battery_powered=True)

        await self.assert_command_successful(message)

        # The battery starts at 100 minutes and is drained by 10% of the 480 minute capacity.
        self.assertEqual(52, drone_member.drone.battery_minutes)

    @cog(battery.BatteryCog)
    async def test_recharge_battery_no_overcharge(self, mocks: Mocks):
        '''
        The recharge battery function should not call
        set_battery_minutes_remaining with more than the maximum capacity (480)
        '''

        drone = mocks.drone('1234', battery_minutes=470)
        await battery.recharge_battery(drone)
        self.assertEqual(drone.battery_minutes, 480)

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_track_active_battery_drain(self, Drone: AsyncMock, mocks: Mocks):
        '''
        For every inactive drone, 1 minute of battery should be drained from them
        via database call 'deincrement_battery_minutes_remaining'.
        Their 'active minutes remaining' should also be deincremented by one.
        '''

        cog = mocks.get_cog()
        cog.draining_batteries = {'1234': 10}
        Drone.load.return_value = mocks.drone('1234')

        await test_utils.start_and_await_loop(cog.track_active_battery_drain)

        self.assertEqual(cog.draining_batteries.get('1234', None), 9)

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_remove_from_active_tracking(self, Drone: AsyncMock, mocks: Mocks):
        '''
        If an inactive drone has 0 minutes of draining left, they should be
        removed from the dictionary.
        '''

        cog = mocks.get_cog()
        cog.draining_batteries = {'1234': 0}

        await test_utils.start_and_await_loop(cog.track_active_battery_drain)

        self.assertIsNone(cog.draining_batteries.get('1234', None))

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_add_drained_role(self, Drone: AsyncMock, mocks: Mocks):
        '''
        Battery module should add the drained role if drone has 0 minutes
        of battery left.
        '''

        drained_role = mocks.role(BATTERY_DRAINED)

        member = mocks.member('1234', roles=[BATTERY_POWERED])
        drone = mocks.drone('1234', battery_minutes=0, discord_id=member.id)
        Drone.all.return_value = [drone]

        await test_utils.start_and_await_loop(mocks.get_cog().track_drained_batteries)

        member.add_roles.assert_called_once_with(drained_role)

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_remove_drained_role(self, Drone: AsyncMock, mocks: Mocks):
        '''
        Battery module should remove the drained role from drones that have it
        if they have more than 0 minutes of charge.
        '''

        drained_role = mocks.role(BATTERY_DRAINED)

        member = mocks.member('1234', roles=[BATTERY_POWERED, BATTERY_DRAINED])
        drone = mocks.drone('1234', discord_id=member.id)
        Drone.all.return_value = [drone]

        await test_utils.start_and_await_loop(mocks.get_cog().track_drained_batteries)

        member.remove_roles.assert_called_once_with(drained_role)

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_warn_low_battery_drones(self, Drone: AsyncMock, mocks: Mocks):
        '''
        The AI Mxtress should warn drones with less than 30 percent battery
        by DMing them.
        '''

        drone_member = mocks.drone_member('1234', drone_is_battery_powered=True)
        drone_member.drone.get_battery_percent_remaining = Mock(return_value=25)
        Drone.all.return_value = [drone_member.drone]

        await test_utils.start_and_await_loop(mocks.get_cog().warn_low_battery_drones)

        drone_member.send.assert_called_once_with("Attention. Your battery is low (30%). Please connect to main power grid in the Storage Facility immediately.")
        self.assertTrue('1234' in mocks.get_cog().low_battery_drones)

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_drone_not_warned_more_than_one(self, Drone: AsyncMock, mocks: Mocks):
        '''
        The AI Mxtress should only DM low battery drones once. If a drone
        has already been warned it should not be warned again until it is
        above 30% battery again.
        '''

        drone = mocks.drone('1234')
        drone.get_battery_percent_remaining = Mock(return_value=30)
        member = mocks.member('1234', roles=[BATTERY_POWERED])
        Drone.all.return_value = [drone]

        battery_cog = mocks.get_cog()
        battery_cog.low_battery_drones = ['1234']

        await test_utils.start_and_await_loop(battery_cog.warn_low_battery_drones)

        member.send.assert_not_called()

    @patch('src.ai.battery.Drone', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_remove_recharged_drones(self, Drone: AsyncMock, mocks: Mocks):
        '''
        The AI Mxtress should remove drones from the list of warned drones
        once they are recharged above 30%.
        '''

        member = mocks.member('1234', roles=[BATTERY_POWERED])
        drone = mocks.drone('1234', discord_id=member.id)
        drone.get_battery_percent_remaining = Mock(return_value=50)
        Drone.all.return_value = [drone]

        battery_cog = mocks.get_cog()
        battery_cog.low_battery_drones = ['1234']

        await test_utils.start_and_await_loop(battery_cog.warn_low_battery_drones)

        member.send.assert_not_called()
        self.assertTrue('1234' not in battery_cog.low_battery_drones)

    @patch('src.ai.battery.DroneMember', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_append_battery_indicator(self, DroneMember: AsyncMock, mocks: Mocks):
        '''
        When passed a message by a battery powered drone, should append
        a battery emoji to the start of their message ([++-]- :: Hello.)
        '''

        original_message = 'Hello.'
        message = mocks.message(None, 'general', original_message)
        message_copy = mocks.message(None, 'general', '')
        drone_member = mocks.drone_member('1234')
        drone_member.drone.is_battery_powered = True
        DroneMember.create.return_value = drone_member

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=100)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f":{emoji.BATTERY_FULL}: :: {original_message}")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=50)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f":{emoji.BATTERY_MID}: :: {original_message}")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=20)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f":{emoji.BATTERY_LOW}: :: {original_message}")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=5)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f":{emoji.BATTERY_EMPTY}: :: {original_message}")

    @patch('src.ai.battery.DroneMember', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_append_battery_indicator_with_prepending(self, DroneMember: AsyncMock, mocks: Mocks):
        '''
        When passed a message by a battery powered drone, should append a
        battery indicator emoji after the drone ID and before the message
        content (5890 :: [++-]- :: Hello.)
        '''

        drone_member = mocks.drone_member('1234', drone_is_battery_powered=True)
        DroneMember.create.return_value = drone_member
        original_message = '1234 :: Hello.\nBeep boop.'
        message = mocks.message(None, 'general', original_message)
        message_copy = mocks.message(None, original_message)

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=100)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"1234 :: :{emoji.BATTERY_FULL}: :: Hello.\nBeep boop.")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=50)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"1234 :: :{emoji.BATTERY_MID}: :: Hello.\nBeep boop.")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=20)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"1234 :: :{emoji.BATTERY_LOW}: :: Hello.\nBeep boop.")

        drone_member.drone.get_battery_percent_remaining = Mock(return_value=5)
        message_copy.content = original_message
        await battery.add_battery_indicator_to_copy(message, message_copy)
        self.assertEqual(message_copy.content, f"1234 :: :{emoji.BATTERY_EMPTY}: :: Hello.\nBeep boop.")

    @patch('src.ai.battery.DroneMember', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_start_battery_drain(self, DroneMember: AsyncMock, mocks: Mocks) -> None:
        '''
        Battery powered drones should have their active tracking minutes
        set to 15 when they first send a message.
        '''

        drone_member = mocks.drone_member('1234', drone_is_battery_powered=True)
        DroneMember.create.return_value = drone_member

        await mocks.get_cog().start_battery_drain(mocks.message(), mocks.message())
        self.assertEqual(mocks.get_cog().draining_batteries.get('1234', None), 15)

    @patch('src.ai.battery.DroneMember', new_callable=AsyncMock)
    @cog(battery.BatteryCog)
    async def test_restart_battery_drain(self, DroneMember: AsyncMock, mocks: Mocks) -> None:
        '''
        Drones that are currently being tracked for battery drain should have
        their minutes reset to 15 if they send another message.
        '''

        cog = mocks.get_cog()
        cog.draining_batteries['1234'] = 6
        DroneMember.create.return_value = mocks.drone_member(1234, drone_is_battery_powered=True)
        await cog.start_battery_drain(mocks.message(), mocks.message())
        self.assertEqual(cog.draining_batteries.get('1234', None), 15)
