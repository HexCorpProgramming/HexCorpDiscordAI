import unittest
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
from datetime import datetime, timedelta

import roles
import channels
import ai.storage as storage
from db.data_objects import Storage, Drone

storage_channel = AsyncMock()

stored_role = Mock()
stored_role.name = roles.STORED

drone_role = Mock()
drone_role.name = roles.DRONE

development_role = Mock()
development_role.name = roles.DEVELOPMENT

hive_mxtress_role = Mock()
hive_mxtress_role.name = roles.HIVE_MXTRESS

bot = AsyncMock()
bot.guilds[0].roles = [stored_role, drone_role, development_role]


class StorageTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        storage_channel.reset_mock()
        bot.reset_mock()

    @patch("ai.storage.fetch_all_storage", return_value=[])
    async def test_storage_report_empty(self, fetch_all_storage):
        await storage.report_storage(storage_channel)
        storage_channel.send.assert_called_once_with('No drones in storage.')

    @patch("ai.storage.fetch_all_storage", return_value=[Storage(str(uuid4()), '9813', '3287', 'trying to break the AI', '', str(datetime.now() + timedelta(hours=4)))])
    async def test_storage_report(self, fetch_all_storage):
        await storage.report_storage(storage_channel)
        storage_channel.send.assert_called_once_with('`Drone #3287`, stored away by `Drone #9813`. Remaining time in storage: 4.0 hours')

    @patch("ai.storage.delete_storage")
    @patch("ai.storage.fetch_drone_with_drone_id", return_value=Drone('3287snowflake', '3287', False, False, '', datetime.now()))
    @patch("ai.storage.fetch_all_elapsed_storage", return_value=[Storage('elapse_storage_id', '9813', '3287', 'trying to break the AI', '⬡-Drone|⬡-Development', str(datetime.now() - timedelta(minutes=4)))])
    async def test_release_timed(self, fetch_all_elapsed_storage, fetch_drone_with_drone_id, delete_storage):
        # setup
        stored_member = AsyncMock()
        bot.guilds[0].get_member.return_value = stored_member

        # run
        await storage.release_timed(bot, stored_role)

        # assert
        bot.guilds[0].get_member.assert_called_once_with('3287snowflake')
        stored_member.remove_roles.assert_called_once_with(stored_role)
        stored_member.add_roles.assert_called_once_with(drone_role, development_role)
        delete_storage.assert_called_once_with('elapse_storage_id')

    async def test_release_unauthorized(self):
        for role in [roles.INITIATE, roles.ASSOCIATE, roles.DRONE, roles.STORED, roles.DEVELOPMENT, roles.ADMIN, roles.MODERATION, roles.SPEECH_OPTIMIZATION, roles.GLITCHED, roles.NITRO_BOOSTER, roles.PATREON_SUPPORTER]:
            # setup
            role_mock = Mock()
            role_mock.name = role

            context = Mock()
            context.author.roles = [role_mock]

            # run & assert
            self.assertFalse(await storage.release(context, None))

    async def test_release_wrong_channel(self):
        channels_to_test = (channels.DRONE_HIVE_CHANNELS + channels.DRONE_DEV_CHANNELS)
        channels_to_test.remove(channels.STORAGE_FACILITY)
        for channel in channels_to_test:
            # setup
            channel_mock = Mock()
            channel_mock.name = channel

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
