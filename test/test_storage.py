import unittest
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
from datetime import datetime, timedelta

import roles
import channels
import ai.storage as storage
from db.data_objects import Storage, Drone
import test.test_utils as test_utils

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
        # setup
        channels_to_test = (channels.DRONE_HIVE_CHANNELS + channels.DRONE_DEV_CHANNELS)
        channels_to_test.remove(channels.STORAGE_FACILITY)
        for channel in channels_to_test:
            message = Mock()
            message.channel.name = channel

            # run & assert
            self.assertFalse(await storage.store_drone(message))

    async def test_storage_message_invalid(self):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "beep boop wants to recharge"
        message.author.roles = [drone_role]

        # run & assert
        self.assertTrue(await storage.store_drone(message))
        message.channel.send.assert_called_once_with(storage.REJECT_MESSAGE)

    @patch("ai.storage.fetch_storage_by_target_id", return_value=Storage('elapse_storage_id', '9813', '3287', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() + timedelta(hours=5))))
    async def test_storage_message_already_in_storage(self, fetch_storage_by_target_id):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 6 :: recharge"
        message.author.roles = [drone_role]

        # run & assert
        self.assertTrue(await storage.store_drone(message))

        fetch_storage_by_target_id.assert_called_once_with('3287')
        message.channel.send.assert_called_once_with("3287 is already in storage.")

    @patch("ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_storage_message_duration_too_long(self, fetch_storage_by_target_id):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 25 :: recharge"
        message.author.roles = [drone_role]

        # run & assert
        self.assertTrue(await storage.store_drone(message))
        fetch_storage_by_target_id.assert_called_once_with('3287')
        message.channel.send.assert_called_once_with("25 is not between 0 and 24.")

    @patch("ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_storage_message_is_Hive_Mxtress(self, fetch_storage_by_target_id):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "5890 :: 0006 :: 1 :: cheeky shenanigans"
        message.author.roles = [drone_role]

        # run & assert
        self.assertTrue(await storage.store_drone(message))
        fetch_storage_by_target_id.assert_called_once_with('0006')
        message.channel.send.assert_called_once_with("You cannot store the Hive Mxtress, silly drone.")

    @patch("ai.storage.datetime")
    @patch("ai.storage.insert_storage")
    @patch("ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_self(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "3287 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

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
        self.assertEqual(inserted.stored_by, "3287")
        self.assertEqual(inserted.target_id, "3287")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by yourself for 8 hours and for the following reason: recharge")

    @patch("ai.storage.datetime")
    @patch("ai.storage.insert_storage")
    @patch("ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone_hive_mxtress(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "0006 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

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
        self.assertEqual(inserted.stored_by, "0006")
        self.assertEqual(inserted.target_id, "3287")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by the Hive Mxtress for 8 hours and for the following reason: recharge")

    @patch("ai.storage.datetime")
    @patch("ai.storage.insert_storage")
    @patch("ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("ai.storage.fetch_storage_by_target_id", return_value=None)
    async def test_store_drone(self, fetch_storage_by_target_id, fetch_drone_with_drone_id, insert_storage, mocked_datetime):
        # setup
        message = AsyncMock()
        message.channel.name = channels.STORAGE_FACILITY
        message.content = "9813 :: 3287 :: 8 :: recharge"
        message.author.roles = [drone_role]
        message.guild.roles = [hive_mxtress_role, drone_role, development_role, stored_role]
        message.guild.channels = [storage_chambers]

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
        self.assertEqual(inserted.stored_by, "9813")
        self.assertEqual(inserted.target_id, "3287")
        self.assertEqual(inserted.purpose, "recharge")
        self.assertEqual(inserted.roles, f"{roles.DRONE}|{roles.DEVELOPMENT}")
        self.assertEqual(inserted.release_time, str(fixed_now + timedelta(hours=8)))
        storage_chambers.send.assert_called_once_with("Greetings <3287mention>. You have been stored away in the Hive Storage Chambers by 9813 for 8 hours and for the following reason: recharge")

    @patch("ai.storage.fetch_all_storage", return_value=[])
    async def test_storage_report_empty(self, fetch_all_storage):
        storage_cog = storage.StorageCog(bot)

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('No drones in storage.')

    @patch("ai.storage.recharge_battery")
    @patch("ai.storage.fetch_all_storage", return_value=[Storage(str(uuid4()), '9813', '3287', 'trying to break the AI', '', str(datetime.now() + timedelta(hours=4)))])
    async def test_storage_report(self, fetch_all_storage, recharge):
        storage_cog = storage.StorageCog(bot)

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('`Drone #3287`, stored away by `Drone #9813`. Remaining time in storage: 4.0 hours')

    @patch("ai.storage.recharge_battery")
    @patch("ai.storage.fetch_all_storage", return_value=[Storage(str(uuid4()), '0006', '3287', 'trying to break the AI', '', str(datetime.now() + timedelta(hours=4)))])
    async def test_storage_report_hive_mxtress(self, fetch_all_storage, recharge_battery):
        storage_cog = storage.StorageCog(bot)

        await test_utils.start_and_await_loop(storage_cog.report_storage)

        storage_cog.storage_channel.send.assert_called_once_with('`Drone #3287`, stored away by the Hive Mxtress. Remaining time in storage: 4.0 hours')

    @patch("ai.storage.delete_storage")
    @patch("ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("ai.storage.fetch_all_elapsed_storage", return_value=[Storage('elapse_storage_id', '9813', '3287', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() - timedelta(minutes=4)))])
    async def test_release_timed(self, fetch_all_elapsed_storage, fetch_drone_with_drone_id, delete_storage):
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
        for role in [roles.INITIATE, roles.ASSOCIATE, roles.DRONE, roles.STORED, roles.DEVELOPMENT, roles.ADMIN, roles.MODERATION, roles.SPEECH_OPTIMIZATION, roles.GLITCHED, roles.NITRO_BOOSTER]:
            # setup
            role_mock = Mock()
            role_mock.name = role

            context = Mock()
            context.author.roles = [role_mock]

            # run & assert
            self.assertFalse(await storage.release(context, None))

    async def test_release_wrong_channel(self):
        # setup
        channels_to_test = (channels.DRONE_HIVE_CHANNELS + channels.DRONE_DEV_CHANNELS)
        channels_to_test.remove(channels.STORAGE_FACILITY)
        for channel in channels_to_test:
            context = Mock()
            context.channel.name = channel
            context.author.roles = [hive_mxtress_role]

            # run & assert
            self.assertFalse(await storage.release(context, None))

    @patch("ai.storage.fetch_storage_by_target_id", return_value=Storage('elapse_storage_id', '9813', '3287', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() + timedelta(hours=5))))
    @patch("ai.storage.convert_id_to_member")
    @patch("ai.storage.delete_storage")
    async def test_release(self, delete_storage, convert_id_to_member, fetch_storage_by_target_id):
        # setup
        context = AsyncMock()
        context.channel.name = channels.STORAGE_FACILITY
        context.author.roles = [hive_mxtress_role]
        context.guild = bot.guilds[0]

        stored_member = AsyncMock()
        bot.guilds[0].get_member.return_value = stored_member

        convert_id_to_member.return_value = stored_member

        # run
        self.assertTrue(await storage.release(context, '3287'))

        # assert
        convert_id_to_member.assert_called_once_with(bot.guilds[0], '3287')
        stored_member.remove_roles.assert_called_once_with(stored_role)
        stored_member.add_roles.assert_called_once_with(drone_role, development_role)
        delete_storage.assert_called_once_with('elapse_storage_id')
