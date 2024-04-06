import unittest
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
from datetime import datetime, timedelta

import src.roles as roles
import src.channels as channels
import src.ai.storage as storage
from src.db.data_objects import Storage, Drone
import test.test_utils as test_utils
import re

storage_channel = AsyncMock()

stored_role = Mock()
stored_role.name = roles.STORED

drone_role = Mock()
drone_role.name = roles.DRONE

development_role = Mock()
development_role.name = roles.DEVELOPMENT

hive_mxtress_role = Mock()
hive_mxtress_role.name = roles.HIVE_MXTRESS

storage_chambers = AsyncMock()
storage_chambers.name = channels.STORAGE_CHAMBERS

bot = AsyncMock()
bot.guilds[0].roles = [stored_role, drone_role, development_role]
bot.guilds[0].channels = [storage_chambers]

storage_cog = storage.StorageCog(bot)


class StorageTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        storage_channel.reset_mock()
        storage_chambers.reset_mock()
        bot.reset_mock()

    async def test_storage_message_wrong_channel(self):
        '''
        Ensure that messages are rejected if sent via a channel other than STORAGE_FACILITY.
        '''

        # setup
        channels_to_test = (channels.DRONE_HIVE_CHANNELS + channels.DRONE_DEV_CHANNELS)
        channels_to_test.remove(channels.STORAGE_FACILITY)
        for channel in channels_to_test:
            message = Mock()
            message.channel.name = channel

            # run & assert
            self.assertFalse(await storage.store_drone(message))

    async def test_storage_message_invalid(self):
        '''
        Ensure that messages are rejected if they are in the wrong format.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "beep boop wants to recharge"
        message.author.roles = [drone_role]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with(storage.REJECT_MESSAGE)

    @patch("src.ai.storage.fetch_storage_by_target_id")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    async def test_storage_message_already_in_storage(self, fetch_drone_with_drone_id, fetch_storage_by_target_id):
        '''
        Ensure that a drone cannot be stored if it is already in storage.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 6 :: recharge"
        message.author.roles = [drone_role]

        fetch_drone_with_drone_id.side_effect = [
            Drone('3288snowflake', '3288', False, False, '', datetime.now()),
            Drone('3287snowflake', '3287', False, False, '', datetime.now())
        ]

        fetch_storage_by_target_id.return_value = Storage('elapse_storage_id', '9813snowflake', '3287snowflake', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() + timedelta(hours=5)))

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        fetch_storage_by_target_id.assert_called_once_with('3287snowflake')
        message.channel.send.assert_called_once_with("3287 is already in storage.")

    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_storage_message_duration_too_long(self, fetch_storage_by_target_id):
        '''
        Ensure that an appropriate error message is given if the storage time is too long.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 24.5 :: recharge"
        message.author.roles = [drone_role]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with("24.5 is not between 0 and 24.")

    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_storage_message_is_Hive_Mxtress(self, fetch_drone_with_drone_id, fetch_storage_by_target_id):
        '''
        Ensure that the Hive Mxtress cannot be stored.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3287 :: 0006 :: 1 :: cheeky shenanigans"
        message.author.roles = [drone_role]

        fetch_drone_with_drone_id.side_effect = [
            Drone('3287snowflake', '3287', False, False, '', datetime.now()),
            None,
        ]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with("You cannot store the Hive Mxtress, silly drone.")

    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_initiator_not_found(self, fetch_storage_by_target_id, fetch_drone_with_drone_id):
        '''
        Ensure that a non-existent initiator is rejected.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3288 :: 3287 :: 1 :: who's this drone?"
        message.author.roles = [drone_role]
        message.author.id = "3287snowflake"

        fetch_drone_with_drone_id.side_effect = [
            None,
            Drone('3287snowflake', '3287', False, False, '', datetime.now())
        ]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with("Initiator drone with ID 3288 could not be found.")

    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_is_forged(self, fetch_storage_by_target_id, fetch_drone_with_drone_id):
        '''
        Ensure that a forged initiator is rejected.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3287 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.author.id = "1865snowflake"
        fetch_drone_with_drone_id.side_effect = [
            Drone('3288snowflake', '3288', False, False, '', datetime.now()),
            Drone('3287snowflake', '3287', False, False, '', datetime.now()),
        ]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with("You are not 3287. Yes, we can indeed tell identical faceless drones apart from each other.")

    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id")
    async def test_storage_drone_not_found(self, fetch_storage_by_target_id, fetch_drone_with_drone_id):
        '''
        Ensure that a non-existent target is rejected.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3287 :: 3288 :: 1 :: who's this drone?"
        message.author.roles = [drone_role]
        message.author.id = "3287snowflake"

        fetch_storage_by_target_id.return_value = None
        fetch_drone_with_drone_id.side_effect = [Drone('3287snowflake', '3287', False, False, '', datetime.now()), None]

        # run & assert
        self.assertFalse(await storage.store_drone(message))
        message.channel.send.assert_called_once_with("Target drone with ID 3288 could not be found.")

    @patch("src.ai.storage.is_free_storage", return_value=True)
    @patch("src.ai.storage.datetime")
    @patch("src.ai.storage.insert_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_self(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime, is_free_storage):
        '''
        Ensure that a drone can store itself.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3287 :: 3287 :: 8.454 :: recharge"
        message.author.roles = [drone_role]
        message.author.id = "3287snowflake"
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

        drone_member = AsyncMock()
        drone_member.roles = [drone_role, development_role]
        drone_member.mention = "<3287mention>"
        message.guild.get_member = Mock(return_value=drone_member)

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        fetch_drone_with_drone_id.side_effect = [
            Drone('3287snowflake', '3287', False, False, '', datetime.now()),
            Drone('3287snowflake', '3287', False, False, '', datetime.now())]

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        message.guild.get_member.assert_called_once_with('3287snowflake')
        drone_member.remove_roles.assert_called_once_with(drone_role, development_role)
        drone_member.add_roles.assert_called_once_with(stored_role)
        inserted = insert_storage.call_args.args[0]
        self.assertEqual(inserted.stored_by, "3287snowflake")
        self.assertEqual(inserted.target_id, "3287snowflake")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8.45)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by yourself for 8.45 hours and for the following reason: recharge")
        message.channel.send.assert_called_once_with("Drone 3287 has been stored away in the Hive Storage Chambers by itself for 8.45 hours and for the following reason: recharge")

    @patch("src.ai.storage.is_free_storage", return_value=True)
    @patch("src.ai.storage.datetime")
    @patch("src.ai.storage.insert_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_hive_mxtress(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime, is_free_storage):
        '''
        Ensure that a drone can be stored by the Hive Mxtress.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "0006 :: 3287 :: 8 :: recharge"
        message.author.id = '0006snowflake'
        message.author.roles = [hive_mxtress_role, drone_role]
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

        drone_member = AsyncMock()
        drone_member.roles = [drone_role, development_role]
        drone_member.mention = "<3287mention>"
        message.guild.get_member = Mock(return_value=drone_member)

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        fetch_drone_with_drone_id.return_value = Drone('3287snowflake', '3287', False, False, '', datetime.now())

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        message.guild.get_member.assert_called_once_with('3287snowflake')
        drone_member.remove_roles.assert_called_once_with(drone_role, development_role)
        drone_member.add_roles.assert_called_once_with(stored_role)
        inserted = insert_storage.call_args.args[0]
        self.assertEqual(inserted.stored_by, None)
        self.assertEqual(inserted.target_id, "3287snowflake")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by the Hive Mxtress for 8 hours and for the following reason: recharge")
        message.channel.send.assert_called_once_with("Drone 3287 has been stored away in the Hive Storage Chambers by the Hive Mxtress for 8 hours and for the following reason: recharge")

    @patch("src.ai.storage.is_free_storage", return_value=True)
    @patch("src.ai.storage.datetime")
    @patch("src.ai.storage.insert_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_free_storage(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime, is_free_storage):
        '''
        Ensure that a drone can store another drone.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.author.id = "9813snowflake"
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

        fetch_drone_with_drone_id.side_effect = [Drone('9813snowflake', '9813', False, False, '', datetime.now()),
                                                 Drone('3287snowflake', '3287', False, False, '', datetime.now())]

        drone_member = AsyncMock()
        drone_member.roles = [drone_role, development_role]
        drone_member.mention = "<3287mention>"
        message.guild.get_member = Mock(return_value=drone_member)

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        message.guild.get_member.assert_called_once_with('3287snowflake')
        drone_member.remove_roles.assert_called_once_with(drone_role, development_role)
        drone_member.add_roles.assert_called_once_with(stored_role)
        inserted = insert_storage.call_args.args[0]
        self.assertEqual(inserted.stored_by, "9813snowflake")
        self.assertEqual(inserted.target_id, "3287snowflake")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by 9813 for 8 hours and for the following reason: recharge")
        message.channel.send.assert_called_once_with("Drone 3287 has been stored away in the Hive Storage Chambers by 9813 for 8 hours and for the following reason: recharge")

    @patch("src.ai.storage.get_trusted_users")
    @patch("src.ai.storage.is_free_storage", return_value=False)
    @patch("src.ai.storage.datetime")
    @patch("src.ai.storage.insert_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_storage_not_allowed(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime, is_free_storage, get_trusted_users):
        '''
        Ensure that a drone cannot store another drone if it is not trusted.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.author.id = "9813snowflake"
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

        fetch_drone_with_drone_id.side_effect = [Drone('9813snowflake', '9813', False, False, '', datetime.now()),
                                                 Drone('3287snowflake', '3287', False, False, '', datetime.now())]

        drone_member = AsyncMock()
        drone_member.roles = [drone_role, development_role]
        drone_member.mention = "<3287mention>"
        message.guild.get_member = Mock(return_value=drone_member)

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        get_trusted_users.return_value = []

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        message.channel.send.assert_called_once_with("Drone 3287 can only be stored by its trusted users or the Hive Mxtress. It has not been stored.")

    @patch("src.ai.storage.get_trusted_users")
    @patch("src.ai.storage.is_free_storage", return_value=True)
    @patch("src.ai.storage.datetime")
    @patch("src.ai.storage.insert_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id")
    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_free_storage_trusted(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime, is_free_storage, get_trusted_users):
        '''
        Ensure that a drone can store another drone if it is trusted.
        '''

        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.author.id = "9813snowflake"
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

        fetch_drone_with_drone_id.side_effect = [Drone('9813snowflake', '9813', False, False, '', datetime.now()),
                                                 Drone('3287snowflake', '3287', False, False, '', datetime.now())]

        drone_member = AsyncMock()
        drone_member.roles = [drone_role, development_role]
        drone_member.mention = "<3287mention>"
        message.guild.get_member = Mock(return_value=drone_member)

        initiator = AsyncMock()
        initiator.id = '9813snowflake'

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        get_trusted_users.return_value = [initiator.id]

        # run & assert
        self.assertFalse(await storage.store_drone(message))

        message.guild.get_member.assert_called_once_with('3287snowflake')
        drone_member.remove_roles.assert_called_once_with(drone_role, development_role)
        drone_member.add_roles.assert_called_once_with(stored_role)
        inserted = insert_storage.call_args.args[0]
        self.assertEqual(inserted.stored_by, "9813snowflake")
        self.assertEqual(inserted.target_id, "3287snowflake")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by 9813 for 8 hours and for the following reason: recharge")
        message.channel.send.assert_called_once_with("Drone 3287 has been stored away in the Hive Storage Chambers by 9813 for 8 hours and for the following reason: recharge")

    @patch("src.ai.storage.fetch_all_storage", return_value=[])
    async def test_storage_report_empty(self, fetch_all_storage):
        '''
        Ensure that the storage report is correct if there are no drones in storage.
        '''

        storage_cog = storage.StorageCog(bot)

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('No drones in storage.')

    @patch("src.ai.storage.recharge_battery")
    @patch("src.ai.storage.fetch_all_storage", return_value=[Storage(str(uuid4()), '9813', '3287', 'trying to break the AI', '', str(datetime.now() + timedelta(hours=4)))])
    @patch("src.ai.storage.fetch_drone_with_id")
    async def test_storage_report(self, fetch_drone_with_id, fetch_all_storage, recharge):
        '''
        Ensure that the storage report correctly reports a drone in storage.
        '''

        storage_cog = storage.StorageCog(bot)
        drones = [
            Drone('9813snowflake', '9813'),
            Drone('3287snowflake', '3287'),
        ]
        fetch_drone_with_id.side_effect = drones

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('`Drone #3287`, stored away by `Drone #9813`. Remaining time in storage: 4.0 hours')

    @patch("src.ai.storage.recharge_battery")
    @patch("src.ai.storage.fetch_all_storage", return_value=[Storage(str(uuid4()), None, '3287', 'trying to break the AI', '', str(datetime.now() + timedelta(hours=4)))])
    @patch("src.ai.storage.fetch_drone_with_id")
    async def test_storage_report_hive_mxtress(self, fetch_drone_with_id, fetch_all_storage, recharge_battery):
        '''
        Ensure that the storage report correctly reports a drone stored by the Hive Mxtress.
        '''

        storage_cog = storage.StorageCog(bot)
        drones = [
            None,
            Drone('3287snowflake', '3287'),
        ]
        fetch_drone_with_id.side_effect = drones

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('`Drone #3287`, stored away by the Hive Mxtress. Remaining time in storage: 4.0 hours')

    @patch("src.ai.storage.delete_storage")
    @patch("src.ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("src.ai.storage.fetch_all_elapsed_storage", return_value=[Storage('elapse_storage_id', '9813snowflake', '3287snowflake', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() - timedelta(minutes=4)))])
    async def test_release_timed(self, fetch_all_elapsed_storage, fetch_drone_with_drone_id, delete_storage):
        '''
        Ensure that a drone is released once the storage time has elapsed.
        '''

        # setup
        stored_member = AsyncMock()
        bot.guilds[0].get_member.return_value = stored_member
        storage_cog = storage.StorageCog(bot)

        # run
        await test_utils.start_and_await_loop(storage_cog.release_timed)

        # assert
        bot.guilds[0].get_member.assert_called_once_with('3287snowflake')
        stored_member.remove_roles.assert_called_once_with(stored_role)
        stored_member.add_roles.assert_called_once_with(drone_role, development_role)
        delete_storage.assert_called_once_with('elapse_storage_id')

    async def test_release_unauthorized(self):
        '''
        Ensure that a drone without a moderator role cannot release a drone from storage.
        '''

        for role in [roles.INITIATE, roles.ASSOCIATE, roles.DRONE, roles.STORED, roles.DEVELOPMENT, roles.SPEECH_OPTIMIZATION, roles.GLITCHED, roles.NITRO_BOOSTER]:
            # setup
            role_mock = Mock()
            role_mock.name = role

            context = Mock()
            context.author.roles = [role_mock]

            # run & assert
            self.assertFalse(await storage.release(context, None))

    @patch("src.ai.storage.fetch_storage_by_target_id", return_value=Storage('elapse_storage_id', '9813snowflake', '3287snowflake', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() + timedelta(hours=5))))
    @patch("src.ai.storage.delete_storage")
    async def test_release(self, delete_storage, fetch_storage_by_target_id):
        '''
        Ensure that a drone with any moderator role can release a stored drone.
        '''

        for role in roles.MODERATION_ROLES:
            # setup
            role_mock = Mock()
            role_mock.name = role

            context = AsyncMock()
            context.channel.name = channels.STORAGE_FACILITY
            context.author.roles = [role_mock]
            context.guild = bot.guilds[0]

            stored_member = AsyncMock()

            # run
            self.assertTrue(await storage.release(context, stored_member))

            # assert
            stored_member.remove_roles.assert_called_once_with(stored_role)
            stored_member.add_roles.assert_called_once_with(drone_role, development_role)
            delete_storage.assert_called_once_with('elapse_storage_id')

            stored_member.reset_mock()
            delete_storage.reset_mock()

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
            [matches] = re.findall(storage.MESSAGE_FORMAT, ' :: '.join(message))
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
            matches = re.findall(storage.MESSAGE_FORMAT, ' :: '.join(message))
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
            self.assertEqual(expected, storage.format_time(time))
