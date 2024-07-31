import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

import src.roles as roles
import src.channels as channels
from src.ai.storage import format_time, MESSAGE_FORMAT, REJECT_MESSAGE, StorageCog, store_drone
from test.cog import cog
from test.mocks import Mocks
import re
from discord.ext.commands import UserInputError
from test.test_utils import start_and_await_loop


class StorageTest(unittest.IsolatedAsyncioTestCase):

    @cog(StorageCog)
    async def asyncSetUp(self, mocks: Mocks):
        self.mocks = mocks
        self.initiator = mocks.member('1234', roles=[self.mocks.role(roles.DRONE), self.mocks.role(roles.DEVELOPMENT)])

    async def test_storage_message_wrong_channel(self):
        '''
        Ensure that messages are rejected if sent via a channel other than STORAGE_FACILITY.
        '''

        channels_to_test = (channels.DRONE_HIVE_CHANNELS + channels.DRONE_DEV_CHANNELS)
        channels_to_test.remove(channels.STORAGE_FACILITY)

        for channel in channels_to_test:
            message = self.mocks.message(self.initiator, channel, 'test')
            self.assertFalse(await store_drone(message))

    async def test_storage_message_invalid(self):
        '''
        Ensure that messages are rejected if they are in the wrong format.
        '''

        # setup
        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, 'beep boop wants to recharge')

        # run & assert
        with self.assertRaisesRegex(UserInputError, re.escape(REJECT_MESSAGE)):
            await store_drone(message)

    @patch('src.ai.storage.DroneMember')
    async def test_storage_message_already_in_storage(self, DroneMember: AsyncMock):
        '''
        Ensure that a drone cannot be stored if it is already in storage.
        '''

        # setup
        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '1234 :: 5678 :: 6 :: recharge')

        DroneMember.find = AsyncMock(side_effect=[self.mocks.drone_member(1234), self.mocks.drone_member(5678, drone_storage=True)])

        # run & assert
        with self.assertRaisesRegex(UserInputError, '5678 is already in storage.'):
            await store_drone(message)

    async def test_storage_message_duration_too_long(self):
        '''
        Ensure that an appropriate error message is given if the storage time is too long.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '1234 :: 5678 :: 24.5 :: recharge')

        with self.assertRaisesRegex(UserInputError, '24.5 is not between 0 and 24.'):
            await store_drone(message)

    @patch('src.ai.storage.DroneMember')
    async def test_storage_message_is_hive_mxtress(self, DroneMember):
        '''
        Ensure that the Hive Mxtress cannot be stored.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '1234 :: 0006 :: 1 :: cheeky shenanigans')

        drone_members = [self.mocks.drone_member(3287), self.mocks.hive_mxtress()]

        DroneMember.find = AsyncMock(side_effect=drone_members)

        # run & assert
        with self.assertRaisesRegex(UserInputError, 'You cannot store the Hive Mxtress, silly drone.'):
            await store_drone(message)

    @patch('src.ai.storage.DroneMember')
    async def test_store_initiator_not_found(self, DroneMember):
        '''
        Ensure that a non-existent initiator is rejected.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '3288 :: 5678 :: 1 :: who\'s this drone?')

        DroneMember.find = AsyncMock(side_effect=[None, self.mocks.drone_member(5678)])

        # run & assert
        with self.assertRaisesRegex(UserInputError, 'Initiator drone with ID 3288 could not be found.'):
            await store_drone(message)

    @patch('src.ai.storage.DroneMember')
    async def test_store_drone_is_forged(self, DroneMember):
        '''
        Ensure that a forged initiator is rejected.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '3288 :: 5678 :: 1 :: incorrect id')

        DroneMember.find = AsyncMock(side_effect=[self.mocks.drone_member(1234), self.mocks.drone_member(5678)])

        # run & assert
        with self.assertRaisesRegex(UserInputError, 'You are not 3288. Yes, we can indeed tell identical faceless drones apart from each other.'):
            await store_drone(message)

    @patch('src.ai.storage.DroneMember')
    async def test_storage_drone_not_found(self, DroneMember):
        '''
        Ensure that a non-existent target is rejected.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '1234 :: 5678 :: 1 :: incorrect id')
        DroneMember.find = AsyncMock(side_effect=[self.mocks.drone_member(1234), None])

        # run & assert
        with self.assertRaisesRegex(UserInputError, 'Target drone with ID 5678 could not be found.'):
            await store_drone(message)

    def assert_stored(self, Storage: MagicMock, message: MagicMock, initiator: MagicMock, target: MagicMock, fixed_now: datetime | None = None) -> None:
        Storage.return_value.insert.assert_called_once()

        initiator_name = 'yourself' if target.id == initiator.id else str(initiator.drone.drone_id)
        initiator_third_person = 'itself' if target.id == initiator.id else str(initiator.drone.drone_id)

        self.mocks.channel(channels.STORAGE_CHAMBERS).send.assert_called_once_with("Greetings " + target.mention + ". You have been stored away in the Hive Storage Chambers by " + initiator_name + " for 8.45 hours and for the following reason: recharge")
        message.channel.send.assert_called_once_with("Drone " + target.drone.drone_id + " has been stored away in the Hive Storage Chambers by " + initiator_third_person + " for 8.45 hours and for the following reason: recharge")

        target.remove_roles.assert_called_once_with(self.mocks.role(roles.DRONE), self.mocks.role(roles.DEVELOPMENT))
        target.add_roles.assert_called_once_with(self.mocks.role(roles.STORED))
        inserted = Storage.call_args.args
        self.assertEqual(inserted[1], initiator.id)
        self.assertEqual(inserted[2], target.id)
        self.assertEqual(inserted[3], "recharge")
        self.assertEqual(inserted[4], [roles.DRONE, roles.DEVELOPMENT])

        if fixed_now is not None:
            self.assertEqual(inserted[5], str(fixed_now + timedelta(hours=8.45)))

    @patch('src.ai.storage.datetime')
    @patch('src.ai.storage.DroneMember')
    @patch('src.ai.storage.Storage')
    async def test_store_drone_self(self, Storage, DroneMember, mocked_datetime):
        '''
        Ensure that a drone can store itself.
        '''

        message = self.mocks.message(self.initiator, channels.STORAGE_FACILITY, '1234 :: 1234 :: 8.45 :: recharge')
        target = self.mocks.drone_member(1234, member=self.initiator)
        DroneMember.find = AsyncMock(side_effect=[target, target])

        storage = AsyncMock()
        Storage.return_value = storage

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        await store_drone(message)

        self.assert_stored(Storage, message, self.initiator, target, fixed_now)

    @patch('src.ai.storage.DroneMember', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_store_drone_hive_mxtress(self, Storage: MagicMock, DroneMember: AsyncMock):
        '''
        Ensure that a drone can be stored by the Hive Mxtress.
        '''

        initiator = self.mocks.hive_mxtress()
        target = self.mocks.drone_member('3287')
        message = self.mocks.message(initiator, channels.STORAGE_FACILITY, '0006 :: 3287 :: 8.45 :: recharge')

        storage = AsyncMock()
        Storage.return_value = storage

        # Hive Mxtress' drone member record uses 'load' instead of 'find'.
        DroneMember.load = AsyncMock(return_value=initiator)
        DroneMember.find = AsyncMock(return_value=target)

        await store_drone(message)

        storage.insert.assert_called_once()

    @patch('src.ai.storage.DroneMember', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_store_drone_free_storage(self, Storage: MagicMock, DroneMember: AsyncMock):
        '''
        Ensure that a drone can store another drone.
        '''

        initiator = self.mocks.drone_member('1234', member=self.initiator)
        target = self.mocks.drone_member('3287', drone_free_storage=True, roles=[roles.DRONE, roles.DEVELOPMENT])
        message = self.mocks.message(initiator, channels.STORAGE_FACILITY, '1234 :: 3287 :: 8.45 :: recharge')

        storage = AsyncMock()
        Storage.return_value = storage

        DroneMember.find = AsyncMock(side_effect=[initiator, target])

        await store_drone(message)

        self.assert_stored(Storage, message, initiator, target)

        storage.insert.assert_called_once()

    @patch('src.ai.storage.DroneMember', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_store_drone_storage_not_allowed(self, Storage: MagicMock, DroneMember: AsyncMock):
        '''
        Ensure that a drone can store another drone.
        '''

        initiator = self.mocks.drone_member('1234', member=self.initiator)
        target = self.mocks.drone_member('3287')
        message = self.mocks.message(initiator, channels.STORAGE_FACILITY, '1234 :: 3287 :: 8.45 :: recharge')

        storage = AsyncMock()
        Storage.return_value = storage

        DroneMember.find = AsyncMock(side_effect=[initiator, target])

        with self.assertRaisesRegex(UserInputError, re.escape('Drone 3287 can only be stored by its trusted users or the Hive Mxtress. It has not been stored.')):
            await store_drone(message)

        storage.insert.assert_not_called()

    @patch('src.ai.storage.DroneMember', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_store_drone_free_storage_trusted(self, Storage: MagicMock, DroneMember: AsyncMock):
        '''
        Ensure that a drone can store another drone.
        '''

        initiator = self.mocks.drone_member('1234', member=self.initiator)
        target = self.mocks.drone_member('3287', drone_free_storage=True, drone_trusted_users=[initiator.id], roles=[roles.DRONE, roles.DEVELOPMENT])
        message = self.mocks.message(initiator, channels.STORAGE_FACILITY, '1234 :: 3287 :: 8.45 :: recharge')

        storage = AsyncMock()
        Storage.return_value = storage

        DroneMember.find = AsyncMock(side_effect=[initiator, target])

        await store_drone(message)

        self.assert_stored(Storage, message, initiator, target)

    @patch('src.ai.storage.Storage')
    async def test_storage_report_empty(self, Storage):
        '''
        Ensure that the storage report is correct if there are no drones in storage.
        '''

        Storage.all = AsyncMock(return_value=[])
        cog = self.mocks.get_cog()

        await start_and_await_loop(cog.report_storage)

        cog.storage_channel.send.assert_called_once_with('No drones in storage.')

    @patch('src.ai.storage.Drone', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_storage_report(self, Storage, Drone):
        '''
        Ensure that the storage report correctly reports a drone in storage.
        '''

        stored = self.mocks.storage(stored_by=11112222, target_id=33334444, purpose='testing', release_time=datetime.now() + timedelta(hours=4))
        Storage.all = AsyncMock(return_value=[stored])
        cog = self.mocks.get_cog()

        initiator = self.mocks.drone(1234)
        stored = self.mocks.drone(5678)

        Drone.load.side_effect = [stored, initiator]

        await start_and_await_loop(cog.report_storage)

        cog.storage_channel.send.assert_called_once_with('`Drone #5678`, stored away by `Drone #1234`. Remaining time in storage: 4.0 hours')

    @patch('src.ai.storage.Drone', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_storage_report_hive_mxtress(self, Storage: MagicMock, Drone: AsyncMock) -> None:
        '''
        Ensure that the storage report correctly reports a drone in storage.
        '''

        stored = self.mocks.storage(stored_by=None, target_id=33334444, purpose='testing', release_time=datetime.now() + timedelta(hours=4))
        Storage.all = AsyncMock(return_value=[stored])
        cog = self.mocks.get_cog()

        Drone.load.side_effect = [self.mocks.drone(5678)]

        await start_and_await_loop(cog.report_storage)

        cog.storage_channel.send.assert_called_once_with('`Drone #5678`, stored away by the Hive Mxtress. Remaining time in storage: 4.0 hours')

    @patch('src.ai.storage.DroneMember', new_callable=AsyncMock)
    @patch('src.ai.storage.Storage')
    async def test_release_timed(self, Storage: MagicMock, DroneMember: AsyncMock) -> None:
        '''
        Ensure that a drone is released once the storage time has elapsed.
        '''

        storage = self.mocks.storage(release_time=datetime.now() + timedelta(hours=4), roles=[roles.DRONE, roles.DEVELOPMENT])
        stored = self.mocks.member('Stored Drone')
        Storage.all_elapsed = AsyncMock(return_value=[storage])
        cog = self.mocks.get_cog()

        DroneMember.load.side_effect = [stored]

        await start_and_await_loop(cog.release_timed)

        storage.delete.assert_called_once()
        stored.remove_roles.assert_called_once_with(self.mocks.role(roles.STORED))
        stored.add_roles.assert_called_once_with(self.mocks.role(roles.DRONE), self.mocks.role(roles.DEVELOPMENT))

    async def test_release_unauthorized(self):
        '''
        Ensure that a drone without a moderator role cannot release a drone from storage.
        '''

        for role in [roles.INITIATE, roles.ASSOCIATE, roles.DRONE, roles.STORED, roles.DEVELOPMENT, roles.SPEECH_OPTIMIZATION, roles.GLITCHED, roles.NITRO_BOOSTER]:
            initiator = self.mocks.member('Member', roles=[role])
            message = self.mocks.command(initiator, channels.STORAGE_CHAMBERS, 'release 1234')

            await self.assert_command_error(message, 'The check functions for command release failed.')

    async def test_release(self):
        '''
        Ensure that a drone with any moderator role can release a stored drone.
        '''

        for role in roles.MODERATION_ROLES:
            initiator = self.mocks.member('Member', roles=[role])
            target = self.mocks.drone_member('5678', drone_storage=self.mocks.storage())
            message = self.mocks.command(initiator, channels.STORAGE_CHAMBERS, 'release 5678')

            await self.assert_command_successful(message)

            target.drone.storage.delete.assert_called_once()

    def test_message_format(self):
        '''
        Ensure that the message regular expression correctly matches or rejects messages.
        '''

        # Ensure that valid messages are accepted.
        messages = [
            ('1234', '5678', '1', 'Test message'),
            ('1234', '5678', '1.', 'Test message'),
            ('1234', '5678', '1.2', 'Test message'),
            ('1234', '5678', '1.23', 'Test message'),
            ('1234', '5678', '1.234', 'Test message'),
            ('1234', '5678', '0.234', 'Test message'),
            ('1234', '5678', '.234', 'Test message'),
        ]

        for message in messages:
            [matches] = re.findall(MESSAGE_FORMAT, ' :: '.join(message))
            self.assertEqual(message, matches)

        # Ensure that invalid messages are rejected.
        messages = [
            # Missing reason text.
            ('1234', '5678', '1', ''),
            # Invalid drone ID.
            ('123', '5678', '1.23', 'Test message'),
            # Invalid target drone ID.
            ('1234', '567', '0.23', 'Test message'),
            # Non-numeric storage time.
            ('1234', '5678', 'one', 'Test message'),
        ]

        for message in messages:
            matches = re.findall(MESSAGE_FORMAT, ' :: '.join(message))
            self.assertEqual(0, len(matches))

    def test_format_time(self):
        '''
        Ensure that time values are formatted correctly.
        '''

        tests = [
            (0, '0'),
            (0.1, '0.1'),
            (0.12, '0.12'),
            (0.123, '0.12'),
            (1, '1'),
            (10, '10'),
            (12.0, '12'),
            (12.1, '12.1'),
            (12.12, '12.12'),
            (12.123, '12.12'),
        ]

        for (time, expected) in tests:
            self.assertEqual(expected, format_time(time))
