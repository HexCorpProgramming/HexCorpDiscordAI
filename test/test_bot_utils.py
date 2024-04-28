from src.bot_utils import get_id
from unittest import IsolatedAsyncioTestCase
from unittest.mock import call, Mock
from src.db.database import change, connect, fetchone, prepare
from asyncio import gather, sleep


class TestBotUtils(IsolatedAsyncioTestCase):

    def test_get_id(self):
        # regular usage
        self.assertEqual(get_id('⬡-Drone #9813'), '9813')
        self.assertEqual(get_id('⬡-Drone #0006'), '0006')
        self.assertEqual(get_id('⬡-Drone #0024'), '0024')
        self.assertEqual(get_id('⬡-Drone #0825'), '0825')
        self.assertEqual(get_id('⬡-Drone #5890'), '5890')
        self.assertEqual(get_id('⬡-Drone #5800'), '5800')
        self.assertEqual(get_id('⬡-Drone #5000'), '5000')

        # ID too long -> gives first valid sequence
        self.assertEqual(get_id('ID too long 56789'), '5678')

        # not a valid ID
        self.assertIsNone(get_id('NotADrone'))
        self.assertIsNone(get_id('ID too short 123'))

        # invalid inputs
        self.assertRaises(TypeError, get_id, None)
        self.assertRaises(TypeError, get_id, 9813)

    async def test_command_race(self):
        '''
        Ensure that the @command decorator registers the command and opens the database connection.
        '''

        ctx = Mock()

        @connect()
        async def do_prepare():
            prepare()

        await do_prepare()

        @connect()
        async def command1(ctx):
            '''
            Simulate a bot command.
            '''

            # Record the database cursor inside the command.
            ctx.log('Inserting drone 1000')
            await change('INSERT INTO drone(discord_id, drone_id) VALUES (1, "1000")')
            ctx.log('Inserted drone 1000')
            await sleep(0.2)
            ctx.log('Rolling back drone 1000')
            raise Exception('Roll back')

        @connect()
        async def command2(ctx):
            '''
            Simulate a bot command.
            '''

            await sleep(0.1)
            ctx.log('Inserting drone 2000')
            await change('INSERT INTO drone(discord_id, drone_id) VALUES (2, "2000")')
            ctx.log('Inserted drone 2000')
            await sleep(0.2)
            ctx.log('Committing drone 2000')

        # Actual order of operations:
        # Start command 1
        # Insert drone 1000.
        # Attempt to start command 2, enter retry loop.
        # Roll back drone 1000.
        # Start command 2.
        # Insert drone 2000.
        # Insert drone 2000.
        # Commit drone 2000.
        #
        # Expected result: drone 2000 is in the database, drone 1000 is not.

        # Run the commands in parallel.
        result = await gather(command1(ctx), command2(ctx), return_exceptions=True)

        self.assertIsInstance(result[0], Exception)
        self.assertIsNone(result[1])

        @connect()
        async def do_check():
            # Check that drone 1000 is not in the database
            self.assertIsNone(await fetchone('SELECT 1 FROM drone WHERE discord_id = 1'))

            # Check that drone 2000 is in the database
            self.assertIsNotNone(await fetchone('SELECT 1 FROM drone WHERE discord_id = 2'))

            # Clean up
            await change('DELETE FROM drone WHERE discord_id = 2')

        await do_check()

        # Ensure that the database functions were called in the order expected.
        expected_calls = [
            call('Inserting drone 1000'),
            call('Inserted drone 1000'),
            call('Rolling back drone 1000'),
            call('Inserting drone 2000'),
            call('Inserted drone 2000'),
            call('Committing drone 2000'),
        ]
        ctx.log.assert_has_calls(expected_calls)
