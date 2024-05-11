import unittest
from unittest.mock import patch, AsyncMock
import discord
from src.ai.emote import generate_big_text, EmoteCog
from test.cog import cog
from test.mocks import Mocks


class TestEmote(unittest.IsolatedAsyncioTestCase):

    mock_guild = AsyncMock(data={"id": 5890}, state=None)

    normal_mock_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "hex_h", "id": 589098133287000006, "require_colons": True, "managed": False})
    extra_custom_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "unnecessary_noise", "id": 216154654256398347, "require_colons": True, "managed": False})
    double_colon_emoji = discord.Emoji(guild=mock_guild, state=None, data={"name": "hex_dc", "id": 589098133287000006, "require_colons": True, "managed": False})

    mock_channel = discord.TextChannel
    mock_channel.guild = mock_guild
    mock_guild.emojis = [normal_mock_emoji, double_colon_emoji, extra_custom_emoji]

    normal_response = str(normal_mock_emoji) * 4

    @patch("src.ai.emote.get", return_value=normal_mock_emoji)
    def test_generate_big_text_generates_big_text_normally(self, mocked_get):

        self.assertEqual(generate_big_text(TestEmote.mock_channel, "beep"), TestEmote.normal_response)
        self.assertEqual(generate_big_text(TestEmote.mock_channel, "boop"), TestEmote.normal_response)
        self.assertEqual(generate_big_text(TestEmote.mock_channel, "    "), TestEmote.normal_response)

    @patch("src.ai.emote.get", return_value=normal_mock_emoji)
    @cog(EmoteCog)
    async def test_return_none_if_generated_text_too_long(self, mocked_get, mocks: Mocks):
        message = mocks.message(None, 'general', 'hc!emote 9813 is such a good development drone that i could write about how wonderful they are and the bigtext generator would return none because there are too many good things to say about it')
        await self.assert_command_error(message)

        message = mocks.message(None, 'general', 'hc!emote and since we need to do two tests i\'d like to mention that 3287 is also a sweet little thing and 5890 always loves to have it around even when it bullies it by calling it a good drone and making it blush')
        await self.assert_command_error(message)

    @patch("src.ai.emote.get", return_value=normal_mock_emoji)
    @cog(EmoteCog)
    async def test_return_none_if_input_contains_no_convertible_material(self, mocked_get, mocks: Mocks):
        message = mocks.message(None, 'general', 'hc!emote ʰᵉʷʷᵒˀˀ')
        await self.assert_command_error(message)

        message = mocks.message(None, 'general', 'hc!emote ᵐʷˢᶦᵗᵉʳ_ᵒᵇᵃᵐᵃˀ')
        await self.assert_command_error(message)

        message = mocks.message(None, 'general', 'hc!emote _____')
        await self.assert_command_error(message)

    @patch("src.ai.emote.get", return_value=normal_mock_emoji)
    def test_generator_removes_custom_emojis_from_input(self, mocked_get):
        self.assertEqual(generate_big_text(TestEmote.mock_channel, f"{str(TestEmote.extra_custom_emoji)}beep{str(TestEmote.extra_custom_emoji)}"), TestEmote.normal_response)

    @patch("src.ai.emote.get", return_value=normal_mock_emoji)
    def test_generator_converts_input_to_lower_case(self, mocked_get):
        self.assertEqual(generate_big_text(TestEmote.mock_channel, "BEEP"), generate_big_text(TestEmote.mock_channel, "beep"))

    def test_two_consecutive_colons_are_converted_to_a_single_emoji(self):
        self.assertEqual(generate_big_text(TestEmote.mock_channel, "::"), str(TestEmote.double_colon_emoji))
        self.assertEqual(generate_big_text(TestEmote.mock_channel, ":::"), str(TestEmote.double_colon_emoji))
