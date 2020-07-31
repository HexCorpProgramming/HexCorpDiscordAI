import discord
import unittest
import ai.amplifier as amp
from unittest.mock import patch
from channels import REPETITIONS
from db.data_objects import Drone


class AmplifierTest(unittest.TestCase):

    mocked_drone = Drone(id="5890")
    mocked_member = discord.Member
    mocked_member.display_name = "heck drone 5890"

    test_guild = discord.Guild(data={"id": 5890}, state=None)

    test_channel = discord.TextChannel(guild=test_guild, state=None, data={"id": 5891, "type": "i 'unno", "name": REPETITIONS, "position": "way at the top"})

    

    @patch("ai.amplifier.get_discord_id_of_drone", return_value=mocked_drone)
    def test_amplifier_generator_returns_drones(self, mocked_dao, mocked_discord):
        
        print("Boop beep.")

        for amp_drone in amp.generate_amplification_information(AmplifierTest.test_channel, ["5890"]):
            print(amp_drone)

        print("Beep boop.")
