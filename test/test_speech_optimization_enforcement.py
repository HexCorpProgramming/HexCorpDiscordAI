import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai.speech_optimization_enforcement import enforce_speech_optimization
from src.channels import CASUAL_CHANNEL, REPETITIONS, MODERATION_CHANNEL
from test.mocks import Mocks

mocks = Mocks()


class TestSpeechOptimizationEnforcement(unittest.IsolatedAsyncioTestCase):
    '''
    The "enforce_speech_optimization" function...
    '''

    def setUp(self) -> None:
        self.author = mocks.drone_member('1234', drone_optimized=True)

    @patch('src.ai.speech_optimization_enforcement.DroneMember')
    async def send(self, msg: str, channel: str, DroneMember: MagicMock) -> bool:
        DroneMember.create = AsyncMock(return_value=self.author)
        self.message = mocks.message(self.author, channel, msg)
        self.message_copy = mocks.message(self.author, channel, msg)

        return await enforce_speech_optimization(self.message, self.message_copy)

    async def test_unoptimized_drone(self) -> None:
        '''
        Should return false if message author is unoptimized.
        '''

        self.author.drone.optimized = False
        msg = 'test message'

        self.assertFalse(await self.send(msg, CASUAL_CHANNEL))
        self.assertEqual(self.message.content, msg)
        self.assertEqual(self.message_copy.content, msg)
        self.message.delete.assert_not_called()

    async def test_optimized_drone_no_status(self) -> None:
        '''
        Should delete the message and return true if no status message found.
        '''

        self.assertTrue(await self.send('1234 :: No status message.', CASUAL_CHANNEL))

        self.message.delete.assert_called_once()

    async def test_optimized_drone_informative_status(self) -> None:
        '''
        Should delete the message and return true if informative status message found.
        '''

        self.assertTrue(await self.send('1234 :: 050 :: An informative status message.', CASUAL_CHANNEL))

        self.message.delete.assert_called_once()

    async def test_optimized_drone_informative_id_status(self) -> None:
        '''
        Should delete the message return true if informative address by ID status message found.
        '''

        self.assertTrue(await self.send('1234 :: 110 :: 9813 :: An informative status message.', CASUAL_CHANNEL))

        self.message.delete.assert_called_once()

    async def test_optimized_drone_mantra(self) -> None:
        '''
        Should return false and not delete message if message is correct mantra in appropriate channel.
        '''

        self.assertFalse(await self.send('1234 :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress.', REPETITIONS))

        self.message.delete.assert_not_called()

    async def test_optimized_drone_blacklisted_channels(self) -> None:
        '''
        Should return false and not delete message if message is in blacklisted channel or category.
        '''

        self.assertFalse(await self.send('1234 :: Drone will not be optimized here.', MODERATION_CHANNEL))

        self.message.delete.assert_not_called()

    async def test_optimized_drone_plain_status(self) -> None:
        '''
        Should not delete the message and return false if message is acceptable plain status code.
        '''

        self.assertFalse(await self.send('1234 :: 200', CASUAL_CHANNEL))

        self.message.delete.assert_not_called()
