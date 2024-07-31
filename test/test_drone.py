from datetime import datetime, timedelta
from src.db.database import change, connect, prepare
from src.db.data_objects import Drone
from unittest import IsolatedAsyncioTestCase
import asyncio
from test.mocks import Mocks
from src.channels import CASUAL_CHANNEL, DRONE_HIVE_CHANNELS, MODERATION_CHANNEL, MODERATION_LOG, OFFICE

mocks = Mocks()


class TestDrone(IsolatedAsyncioTestCase):

    drone: Drone

    @classmethod
    def setUpClass(cls):
        asyncio.run(TestDrone.setUpDatabase())

    @classmethod
    @connect()
    async def setUpDatabase(cls):
        '''
        Initialize the database schema in "test.db" before running the tests.
        '''

        prepare()

    @connect()
    async def asyncSetUp(self) -> None:
        '''
        Delete any existing records and insert a new test record.
        '''

        await change('DELETE FROM drone')

        drone = Drone()

        drone.discord_id = 123456789012345
        drone.drone_id = '1234'
        drone.optimized = True
        drone.glitched = True
        drone.trusted_users = [111111, 222222, 333333]
        drone.last_activity = datetime.now()
        drone.id_prepending = True
        drone.identity_enforcement = True
        drone.third_person_enforcement = True
        drone.can_self_configure = True
        drone.temporary_until = datetime.now() + timedelta(minutes=30)
        drone.is_battery_powered = True
        drone.battery_type_id = 3
        drone.battery_minutes = 123
        drone.free_storage = True
        drone.associate_name = 'An Associate'

        drone.battery_type = mocks.battery_type(id=3)

        await drone.insert()

        self.drone = drone

    @connect()
    async def test_load(self) -> None:
        '''
        Ensure that the drone record can be loaded correctly.
        '''

        loaded = await Drone.load(123456789012345)

        self.assertEqual(self.drone.discord_id, loaded.discord_id)
        self.assertEqual(self.drone.drone_id, loaded.drone_id)
        self.assertEqual(self.drone.optimized, loaded.optimized)
        self.assertEqual(self.drone.glitched, loaded.glitched)
        self.assertEqual(self.drone.trusted_users, loaded.trusted_users)
        self.assertEqual(self.drone.last_activity, loaded.last_activity)
        self.assertEqual(self.drone.id_prepending, loaded.id_prepending)
        self.assertEqual(self.drone.identity_enforcement, loaded.identity_enforcement)
        self.assertEqual(self.drone.third_person_enforcement, loaded.third_person_enforcement)
        self.assertEqual(self.drone.can_self_configure, loaded.can_self_configure)
        self.assertEqual(self.drone.temporary_until, loaded.temporary_until)
        self.assertEqual(self.drone.is_battery_powered, loaded.is_battery_powered)
        self.assertEqual(self.drone.battery_type_id, loaded.battery_type_id)
        self.assertEqual(self.drone.battery_minutes, loaded.battery_minutes)
        self.assertEqual(self.drone.free_storage, loaded.free_storage)
        self.assertEqual(self.drone.associate_name, loaded.associate_name)

    @connect()
    async def test_save(self) -> None:
        '''
        Ensure that the drone record can be updated correctly.
        '''

        until = datetime(year=2026, month=6, day=3, hour=1, minute=2, second=3)
        self.drone.is_battery_powered = False
        self.drone.temporary_until = until
        await self.drone.save()

        loaded = await Drone.load(self.drone.discord_id)

        self.assertFalse(loaded.is_battery_powered)
        self.assertEqual(loaded.temporary_until, until)

    @connect()
    async def test_all(self) -> None:
        '''
        Ensure that all drone records can be loaded.
        '''

        # Insert some more drones.
        self.drone.discord_id = 1
        self.drone.drone_id = '1'
        await self.drone.insert()

        self.drone.discord_id = 2
        self.drone.drone_id = '2'
        await self.drone.insert()

        all = await Drone.all()

        # Records will be returned ordered by primary key.
        self.assertEqual(3, len(all))
        self.assertEqual(1, all[0].discord_id)
        self.assertEqual(2, all[1].discord_id)
        self.assertEqual(123456789012345, all[2].discord_id)

    @connect()
    async def test_find(self) -> None:
        '''
        Ensure that a single record can be found by Discord ID.
        '''

        loaded = await Drone.find(discord_id=123456789012345)

        self.assertEqual(loaded.drone_id, '1234')

    @connect()
    async def test_find_unsuccessful(self) -> None:
        '''
        Ensure that find returns None if a record is not found by Discord ID.
        '''

        self.assertIsNone(await Drone.find(discord_id=0))

    @connect()
    async def test_find_no_idea(self) -> None:
        '''
        Ensure that find throws if no drone or discord ID is given.
        '''

        with self.assertRaises(Exception):
            await Drone.find(wrong=1)

    @connect()
    async def test_drone_find(self) -> None:
        '''
        Ensure that a single record can be found by Drone ID.
        '''

        loaded = await Drone.find(drone_id='1234')

        self.assertEqual(loaded.drone_id, '1234')

    @connect()
    async def test_find_drone_unsuccessful(self) -> None:
        '''
        Ensure that find returns None if a record is not found by Drone ID.
        '''

        self.assertIsNone(await Drone.find(drone_id='0000'))

    @connect()
    async def test_find_by_member(self) -> None:
        '''
        Ensure that a single record can be found by a Discord Member object.
        '''

        member = mocks.member('name', id=123456789012345)
        loaded = await Drone.find(member=member)

        self.assertEqual(loaded.drone_id, '1234')

    def test_allows_configuration_by_hive_mxtress(self) -> None:
        '''
        Ensure that the Hive Mxtress can always configure a drone.
        '''

        self.assertTrue(self.drone.allows_configuration_by(mocks.hive_mxtress()))

    def test_allows_configuration_by_trusted_user(self) -> None:
        '''
        Ensure that a trusted user can configure the drone.
        '''

        user = mocks.drone_member('5555', id=222222)

        self.assertTrue(self.drone.allows_configuration_by(user))

    def test_allows_configuration_by_self(self) -> None:
        '''
        Ensure that a drone can configure itself if allowed.
        '''

        user = mocks.drone_member('1234', id=self.drone.discord_id, drone_can_self_configure=True)

        self.assertTrue(self.drone.allows_configuration_by(user))

    def test_disallows_configuration_by_self(self) -> None:
        '''
        Ensure that a drone cannot configure itself if disallowed.
        '''

        self.drone.can_self_configure = False
        user = mocks.drone_member('1234', id=self.drone.discord_id)

        self.assertFalse(self.drone.allows_configuration_by(user))

    def test_disallows_configuration_by_anyone(self) -> None:
        '''
        Ensure that a drone cannot be configured by an untrusted member.
        '''

        user = mocks.drone_member('1234', id=9)

        self.assertFalse(self.drone.allows_configuration_by(user))

    def test_allows_storage_by_hive_mxtress(self) -> None:
        '''
        Ensure that a drone can be stored by the Hive Mxtress.
        '''

        self.assertTrue(self.drone.allows_storage_by(mocks.hive_mxtress()))

    def test_allows_storage_by_trusted_user(self) -> None:
        '''
        Ensure that a drone can be stored by a trusted user.
        '''

        user = mocks.drone_member('5555', id=222222)
        self.assertTrue(self.drone.allows_storage_by(user))

    def test_allows_storage_by_self(self) -> None:
        '''
        Ensure that a drone can be stored by itself.
        '''

        user = mocks.drone_member('1234', id=self.drone.discord_id)
        self.assertTrue(self.drone.allows_storage_by(user))

    def test_disallows_storage_by_untrusted_user(self) -> None:
        '''
        Ensure that a drone cannot be stored by an untrusted user if free storage is disabled.
        '''

        self.drone.free_storage = False
        user = mocks.drone_member('5555', id=9)
        self.assertFalse(self.drone.allows_storage_by(user))

    def test_allows_storage_by_untrusted_user(self) -> None:
        '''
        Ensure that a drone can be stored by an untrusted user if free storage is enabled.
        '''

        self.drone.free_storage = True
        user = mocks.drone_member('5555', id=9)
        self.assertTrue(self.drone.allows_storage_by(user))

    def test_is_configured(self) -> None:
        '''
        Ensure that a drone can report if it is configured or not.
        '''

        options = [
            'optimized',
            'glitched',
            'id_prepending',
            'identity_enforcement',
            'third_person_enforcement',
            'is_battery_powered',
        ]

        for option in options:
            setattr(self.drone, option, False)

        self.assertFalse(self.drone.is_configured())

        for set_option in options:
            for option in options:
                setattr(self.drone, option, option == set_option)

            self.assertTrue(self.drone.is_configured())

    def test_get_battery_percent_remaining(self) -> None:
        '''
        Ensure that the battery percentage remaining is correct.
        '''

        self.drone.battery_type.capacity = 1000

        self.drone.battery_minutes = 0
        self.assertEqual(0, self.drone.get_battery_percent_remaining())

        self.drone.battery_minutes = 10
        self.assertEqual(1, self.drone.get_battery_percent_remaining())

        self.drone.battery_minutes = 500
        self.assertEqual(50, self.drone.get_battery_percent_remaining())

        self.drone.battery_minutes = 1000
        self.assertEqual(100, self.drone.get_battery_percent_remaining())

    def test_third_person_enforcable_no_channel(self) -> None:
        '''
        Ensure that third person pronouns are not enforced in direct message.
        '''

        self.drone.third_person_enforcement = True
        self.assertFalse(self.drone.third_person_enforcable(None))

    def test_third_person_enforcable_non_hive_channel(self) -> None:
        '''
        Ensure that third person pronouns are not enforced by default in non-hive channels.
        '''

        self.drone.third_person_enforcement = False
        self.assertFalse(self.drone.third_person_enforcable(mocks.channel(CASUAL_CHANNEL)))

    def test_third_person_enforcable_non_hive_channel_disabled(self) -> None:
        '''
        Ensure that third person pronouns are enforced if enabled in non-drone hive channels.
        '''

        self.drone.third_person_enforcement = True

        self.assertTrue(self.drone.third_person_enforcable(mocks.channel(CASUAL_CHANNEL)))

    def test_third_person_enforcable_moderation_channel(self) -> None:
        '''
        Ensure that third person pronouns are not enforced in moderation channels.
        '''

        self.drone.third_person_enforcement = True

        for channel in [MODERATION_CHANNEL, MODERATION_LOG, OFFICE]:
            self.assertFalse(self.drone.third_person_enforcable(mocks.channel(channel)))

    def test_third_person_enforcable_drone_hive_channels(self) -> None:
        '''
        Ensure that third person pronouns are always enforced in drone hive channels.
        '''

        self.drone.third_person_enforcement = False

        for channel in DRONE_HIVE_CHANNELS:
            self.assertTrue(self.drone.third_person_enforcable(mocks.channel(channel)))

    def test_identity_enforcable_no_channel(self) -> None:
        '''
        Ensure that identity is not enforced in direct message.
        '''

        self.drone.identity_enforcement = True
        self.assertFalse(self.drone.identity_enforcable(None))

    def test_identity_enforcable_non_hive_channel(self) -> None:
        '''
        Ensure that identity is not enforced by default in non-hive channels.
        '''

        self.drone.identity_enforcement = False
        self.assertFalse(self.drone.identity_enforcable(mocks.channel(CASUAL_CHANNEL)))

    def test_identity_enforcable_non_hive_channel_disabled(self) -> None:
        '''
        Ensure that identity is enforced if enabled in non-drone hive channels.
        '''

        self.drone.identity_enforcement = True

        self.assertTrue(self.drone.identity_enforcable(mocks.channel(CASUAL_CHANNEL)))

    def test_identity_enforcable_moderation_channel(self) -> None:
        '''
        Ensure that identity is not enforced in moderation channels.
        '''

        self.drone.identity_enforcement = True

        for channel in [MODERATION_CHANNEL, MODERATION_LOG, OFFICE]:
            self.assertFalse(self.drone.identity_enforcable(mocks.channel(channel)))

    def test_identity_enforcable_drone_hive_channels(self) -> None:
        '''
        Ensure that identity is always enforced in drone hive channels.
        '''

        self.drone.identity_enforcement = False

        for channel in DRONE_HIVE_CHANNELS:
            self.assertTrue(self.drone.identity_enforcable(mocks.channel(channel)))
