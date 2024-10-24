import unittest
from datetime import datetime, timedelta
from src.db.timer import Timer
from src.db.database import connect
from test.mocks import Mocks
from src.db.data_objects import Drone


class TimerTest(unittest.IsolatedAsyncioTestCase):

    @connect()
    async def test_all_elapsed(self) -> None:
        mocks = Mocks()
        guild = mocks.get_guild()

        # Insert some drones into the database.
        drone_1 = Drone(discord_id=1, drone_id='3344')
        drone_2 = Drone(discord_id=2, drone_id='4455')
        await drone_1.insert()
        await drone_2.insert()

        # Add matching Discord members to the guild.
        mocks.member(id=1)
        mocks.member(id=2)

        # Create a timer that has elapsed and should be returned.
        elapsed = Timer('test-elapsed', drone_1.discord_id, 'glitched', datetime.now() - timedelta(minutes=2))
        await elapsed.insert()

        # Create a timer that has not elapsed and should not be returned.
        not_elapsed = Timer('test-not-elapsed', drone_2.discord_id, 'glitched', datetime.now() + timedelta(minutes=2))
        await not_elapsed.insert()

        # Fetch the DroneMember records of users whose timers have elapsed.
        members = await Timer.all_elapsed(guild)

        # Check that only the elapsed timer is returned.
        self.assertIn(elapsed.discord_id, [t.id for t in members])
        self.assertNotIn(not_elapsed.discord_id, [t.id for t in members])

        # Delete the database records that were inserted.
        await elapsed.delete()
        await not_elapsed.delete()
        await drone_1.delete()
        await drone_2.delete()
