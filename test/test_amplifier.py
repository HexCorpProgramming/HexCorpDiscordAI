import discord
import unittest
import ai.amplifier as amp
from unittest.mock import patch, PropertyMock, Mock
from channels import REPETITIONS
from db.data_objects import Drone

mocked_drone = Drone(id="5890")

mocked_member = discord.Member
mocked_member.display_name = "heck drone 5890"

test_guild = Mock()
test_guild.get_member.return_value = mocked_member

test_channel = PropertyMock()
test_channel.guild = test_guild
test_channel.name = REPETITIONS


class AmplifierTest(unittest.TestCase):

    @patch("ai.amplifier.get_discord_id_of_drone", return_value=mocked_drone)
    @patch("ai.amplifier.has_role", return_value=False)
    def test_amplifier_generator_returns_drones(self, mocked_dao, mocked_get):

        print("Boop beep.")

        for amp_drone in amp.generate_amplification_information(test_channel, ["5890"]):
            print(amp_drone)

        print("Beep boop.")
