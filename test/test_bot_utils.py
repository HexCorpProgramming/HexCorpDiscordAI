from src.bot_utils import get_id
from unittest import IsolatedAsyncioTestCase


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
