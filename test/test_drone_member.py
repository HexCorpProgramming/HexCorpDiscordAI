from discord.ext.commands import BadArgument
from src.drone_member import DroneMember
from test.mocks import Mocks
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

mocks = Mocks()


class TestDroneMember(IsolatedAsyncioTestCase):

    drone_member: DroneMember

    def create_context(self) -> MagicMock:
        self.drone_member = mocks.drone_member('1234')
        ctx = MagicMock
        ctx.bot = False
        ctx.guild = mocks.get_guild()
        ctx.message = mocks.message(mocks.hive_mxtress(), 'general', 'test')

        return ctx

    @patch('src.drone_member.Drone', new_callable=AsyncMock)
    async def test_convert(self, Drone: AsyncMock):
        '''
        Ensure that a Discord ID is converted to a memeber.
        '''

        Drone.find.return_value = None
        ctx = self.create_context()
        ctx.message.mentions = [self.drone_member]
        found_member = await DroneMember.convert(ctx, str(self.drone_member.id))

        self.assertEqual(self.drone_member.id, found_member.id)

    @patch('src.drone_member.Drone', new_callable=AsyncMock)
    async def test_convert_invalid_id(self, Drone: AsyncMock):
        '''
        Ensure that anything other than a drone ID is rejected.
        '''

        Drone.find.return_value = None
        ctx = self.create_context()

        for arg in ['123, 12345', 'test']:
            with self.assertRaises(BadArgument):
                await DroneMember.convert(ctx, arg)

    @patch('src.drone_member.Drone', new_callable=AsyncMock)
    async def test_convert_non_drone(self, Drone: AsyncMock):
        '''
        Ensure that an unassigned drone ID is rejected.
        '''

        Drone.find.return_value = None
        ctx = self.create_context()

        with self.assertRaises(BadArgument):
            await DroneMember.convert(ctx, '5555')

    @patch('src.drone_member.Drone', new_callable=AsyncMock)
    async def test_convert_deleted_member(self, Drone):
        '''
        Ensure that an orphaned drone record is rejected.
        '''

        # Create a Drone but no associated Member.
        drone = mocks.drone('6666')
        Drone.find.return_value = drone
        ctx = self.create_context()

        with self.assertRaises(BadArgument):
            await DroneMember.convert(ctx, '6666')

    @patch('src.drone_member.Drone', new_callable=AsyncMock)
    async def test_convert_drone_id(self, Drone):
        '''
        Ensure that a drone ID can be used.
        '''

        ctx = self.create_context()
        Drone.find.return_value = self.drone_member.drone

        found_member = await DroneMember.convert(ctx, self.drone_member.drone.drone_id)

        self.assertEqual(found_member.id, self.drone_member.id)
