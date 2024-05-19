import unittest
from src.ai.emote import generate_big_text, EmoteCog
from test.cog import cog
from test.mocks import Mocks


class TestEmote(unittest.IsolatedAsyncioTestCase):

    mocks = Mocks()
    channel = mocks.channel('general')

    def test_generate_big_text_generates_big_text_normally(self):

        self.assertEqual(generate_big_text(TestEmote.channel, "beep"), ':hex_b::hex_e::hex_e::hex_p:')
        self.assertEqual(generate_big_text(TestEmote.channel, "boop"), ':hex_b::hex_o::hex_o::hex_p:')
        self.assertEqual(generate_big_text(TestEmote.channel, "    "), ':blank::blank::blank::blank:')

    @cog(EmoteCog)
    async def test_return_none_if_generated_text_too_long(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote 9813 is such a good development drone that i could write about how wonderful they are and the bigtext generator would return none because there are too many good things to say about it')
        await self.assert_command_error(message)

        message = mocks.command(None, 'general', 'emote and since we need to do two tests i\'d like to mention that 3287 is also a sweet little thing and 5890 always loves to have it around even when it bullies it by calling it a good drone and making it blush')
        await self.assert_command_error(message)

    @cog(EmoteCog)
    async def test_return_none_if_input_contains_no_convertible_material(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote ʰᵉʷʷᵒˀˀ')
        await self.assert_command_error(message)

        message = mocks.command(None, 'general', 'emote ᵐʷˢᶦᵗᵉʳ_ᵒᵇᵃᵐᵃˀ')
        await self.assert_command_error(message)

        message = mocks.command(None, 'general', 'emote _____')
        await self.assert_command_error(message)

    def test_generator_removes_custom_emojis_from_input(self):
        custom_emoji = '<:custom:012345678901234567>'
        self.assertEqual(generate_big_text(TestEmote.channel, f"{custom_emoji}beep{custom_emoji}"), ':hex_b::hex_e::hex_e::hex_p:')

    def test_generator_converts_input_to_lower_case(self):
        self.assertEqual(generate_big_text(TestEmote.channel, "BEEP"), generate_big_text(TestEmote.channel, "beep"))

    def test_two_consecutive_colons_are_converted_to_a_single_emoji(self):
        self.assertEqual(generate_big_text(TestEmote.channel, "::"), str(self.mocks.emoji('hex_dc')))
        self.assertEqual(generate_big_text(TestEmote.channel, ":::"), str(self.mocks.emoji('hex_dc')))
