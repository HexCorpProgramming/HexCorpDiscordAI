import unittest
from unittest.mock import patch
import discord
from ai.emote import generate_big_text
from channels import HIVE_COORDINATION


class TestEmote(unittest.TestCase):

    def test_generate_big_text(self):

        self.maxDiff = 2000

        mock_channel = discord.TextChannel
        mock_guild = discord.Guild(data={"id": 5890}, state=None)
        mock_channel.guild = mock_guild

        normal_mock_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "hex_h", "id": 589098133287000006, "require_colons": True, "managed": False})
        double_colon_mock_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "hex_dc", "id": 589098133287000006, "require_colons": True, "managed": False})

        normal_response = f"> {str(normal_mock_emoji)*4}"

        # Mocking get() to always return a valid emoji for Testing Purposes.
        with patch('ai.emote.get', return_value=normal_mock_emoji):

            # Happy path
            self.assertEqual(generate_big_text(mock_channel, "beep"), normal_response)
            self.assertEqual(generate_big_text(mock_channel, "boop"), normal_response)
            self.assertEqual(generate_big_text(mock_channel, "    "), normal_response)

            # Message too long
            self.assertEqual(generate_big_text(mock_channel, "9813 is such a good development drone that i could write about how wonderful they are and the bigtext generator would return none because there are too many good things to say about it"), None)
            self.assertEqual(generate_big_text(mock_channel, "and since we need to do two tests i'd like to mention that 3287 is also a sweet little thing and 5890 always loves to have it around even when it bullies it by calling it a good drone and making it blush"), None)

            # Message has no valid characters
            self.assertEqual(generate_big_text(mock_channel, "ʰᵉʷʷᵒˀˀ"), None)
            self.assertEqual(generate_big_text(mock_channel, "ᵐʷˢᶦᵗᵉʳ_ᵒᵇᵃᵐᵃˀ"), None)
            self.assertEqual(generate_big_text(mock_channel, "_____"), None)

            # Test that the generate_big_text function cleans out excess custom emoji at the start
            extra_custom_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "unnecessary_noise", "id": 216154654256398347, "require_colons": True, "managed": False})
            self.assertEqual(generate_big_text(mock_channel, f"{str(extra_custom_emoji)}beep{str(extra_custom_emoji)}"), normal_response)

        mock_guild.emojis = [normal_mock_emoji, double_colon_mock_emoji]

        # Double colon functionality (two double colons become one double colon emoji)
        self.assertEqual(generate_big_text(mock_channel, "::"), f"> {str(double_colon_mock_emoji)}")