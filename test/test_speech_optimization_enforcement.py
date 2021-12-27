import unittest
from unittest.mock import AsyncMock, patch
from ai.speech_optimization_enforcement import enforce_speech_optimization
from ai.data_objects import MessageCopy
from channels import REPETITIONS, MODERATION_CHANNEL


class TestSpeechOptimizationEnforcement(unittest.IsolatedAsyncioTestCase):
    '''
    The "enforce_speech_optimization function...
    '''

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=False)
    async def test_unoptimized_drone(self, optimized):
        '''
        should return false if message author is unoptimized.
        '''

        message = AsyncMock()
        message_copy = MessageCopy()

        self.assertFalse(await enforce_speech_optimization(message, message_copy))

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_no_status(self, optimized):
        '''
        should delete the message and return true if no status message found.
        '''

        message = AsyncMock()
        message.content = "5890 :: No status message."
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertTrue(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_called_once()

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_informative_status(self, optimized):
        '''
        should delete the message and return true if informative status message found.
        '''

        message = AsyncMock()
        message.content = "5890 :: 050 :: An informative status message."
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertTrue(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_called_once()

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_informative_id_status(self, optimized):
        '''
        should delete the message and return true if informative address by ID status message found.
        '''

        message = AsyncMock()
        message.content = "5890 :: 110 :: 9813 :: An informative status message."
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertTrue(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_called_once()

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_mantra(self, optimized):
        '''
        should return false and not delete message if message is correct mantra in appropriate channel.
        '''
        message = AsyncMock()
        message.content = "5890 :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress."
        message.channel.name = REPETITIONS
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertFalse(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_not_called()

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_blacklisted_channels(self, optimized):
        '''
        should return false and not delete message if message is in blacklisted channel or category.
        '''

        message = AsyncMock()
        message.content = "5890 :: Drone will not be optimized here."
        message.channel.name = MODERATION_CHANNEL
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertFalse(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_not_called()

    @patch("ai.speech_optimization_enforcement.is_optimized", return_value=True)
    async def test_optimized_drone_plain_status(self, optimized):
        '''
        should not delete the message and return false if message is acceptable plain status code.
        '''

        message = AsyncMock()
        message.content = "5890 :: 200"
        message.author.display_name = "5890"

        message_copy = MessageCopy(content=message.content)

        self.assertFalse(await enforce_speech_optimization(message, message_copy))
        message.delete.assert_not_called()
