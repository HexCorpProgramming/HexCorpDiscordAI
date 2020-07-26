from bot_utils import get_id
import unittest


class TestBotUtils(unittest.TestCase):

    def test_get_id(self):
        self.assertEqual(get_id('⬡-Drone #9813'), '9813')
        self.assertEqual(get_id('⬡-Drone #0006'), '0006')
        self.assertEqual(get_id('⬡-Drone #0024'), '0024')
        self.assertEqual(get_id('⬡-Drone #0825'), '0825')
        self.assertEqual(get_id('⬡-Drone #5890'), '5890')
        self.assertEqual(get_id('⬡-Drone #5800'), '5800')
        self.assertEqual(get_id('⬡-Drone #5000'), '5000')

        self.assertEqual(get_id('ID too long 56789'), '5678')

        self.assertIsNone(get_id('NotADrone'))
