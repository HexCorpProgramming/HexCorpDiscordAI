import unittest
from unittest.mock import Mock
from main import amplify

class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    async def test_webhook_called_with_appropriate_message(self):

        context = Mock()
        message = "Beep boop!"
        target_channel = Mock()

        await amplify(context, message, target_channel)
