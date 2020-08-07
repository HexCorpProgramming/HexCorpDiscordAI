import unittest
import ai.amplifier as amp
from unittest.mock import patch, PropertyMock, Mock
from channels import REPETITIONS
from resources import DRONE_AVATAR

test_guild = Mock()

mocked_member_1 = Mock()
mocked_member_1.display_name = "⬡-Drone #0077"

mocked_member_2 = Mock()
mocked_member_2.display_name = "⬡-Drone #5890"

test_channel = PropertyMock()
test_channel.guild = test_guild
test_channel.name = REPETITIONS


class AmplifierTest(unittest.TestCase):

    def setUp(self):
        # Reset the get_member return values (prevents dirtying context between tests).
        test_guild.get_member.side_effect = [mocked_member_1, mocked_member_2]

    @patch("ai.amplifier.convert_id_to_member", side_effect=[mocked_member_1, mocked_member_2])
    def test_amplifier_generator_returns_profile_dictionaries(self, mocked_role_check, mocked_id_converter):
        self.assertEqual(next(amp.generate_amplification_information(test_channel, ["0077"]))["username"], "⬡-Drone #0077")
        self.assertEqual(next(amp.generate_amplification_information(test_channel, ["5890"]))["username"], "⬡-Drone #5890")

    @patch("ai.amplifier.convert_id_to_member", side_effect=[mocked_member_1, mocked_member_2])
    def test_amplifier_generator_returns_drone_icons_if_in_hive(self, mocked_role_check, mocked_id_converter):

        test_channel.name = "NOT A HIVE CHANNEL!!!"
        self.assertNotEqual(next(amp.generate_amplification_information(test_channel, ["0077"]))["avatar_url"], DRONE_AVATAR)

        test_channel.name = REPETITIONS
        self.assertEqual(next(amp.generate_amplification_information(test_channel, ["0077"]))["avatar_url"], DRONE_AVATAR)

    def test_amplifier_generator_yields_none_on_non_drone_ids(self):
        self.assertIsNone(next(amp.generate_amplification_information(test_channel, ["SILLY ORGANIC HUMAN"])))
