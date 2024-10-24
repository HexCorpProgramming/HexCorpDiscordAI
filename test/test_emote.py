import unittest
from src.channels import DRONETALK
from src.ai.emote import EmoteCog
from test.cog import cog
from test.mocks import Mocks


class TestEmote(unittest.IsolatedAsyncioTestCase):

    @cog(EmoteCog)
    async def test_generate_big_text_generates_big_text_normally(self, mocks: Mocks):

        message = mocks.command(None, 'general', 'emote beep')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_b::hex_e::hex_e::hex_p:')

        message = mocks.command(None, 'general', 'emote boop')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_b::hex_o::hex_o::hex_p:')

        message = mocks.command(None, 'general', 'emote o    o')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_o::blank::blank::blank::blank::hex_o:')

    @cog(EmoteCog)
    async def test_reject_drone_hive_channels(self, mocks: Mocks):
        message = mocks.command(None, DRONETALK, 'emote beep')
        await self.assert_command_error(message, 'This command cannot be used in drone hive channels.')

    @cog(EmoteCog)
    async def test_return_none_if_generated_text_too_long(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote 9813 is such a good development drone that i could write about how wonderful they are and the bigtext generator would return none because there are too many good things to say about it. xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        await self.assert_command_error(message, 'Message is too long.')

        message = mocks.command(None, 'general', 'emote and since we need to do two tests i\'d like to mention that 3287 is also a sweet little thing and 5890 always loves to have it around even when it bullies it by calling it a good drone and making it blush. xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        await self.assert_command_error(message, 'Message is too long.')

    @cog(EmoteCog)
    async def test_return_none_if_input_contains_no_convertible_material(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote ʰᵉʷʷᵒˀˀ')
        await self.assert_command_error(message)

        message = mocks.command(None, 'general', 'emote ᵐʷˢᶦᵗᵉʳ_ᵒᵇᵃᵐᵃˀ')
        await self.assert_command_error(message)

        message = mocks.command(None, 'general', 'emote _____')
        await self.assert_command_error(message)

    @cog(EmoteCog)
    async def test_generator_removes_custom_emojis_from_input(self, mocks: Mocks):
        custom_emoji = '<:custom:012345678901234567>'
        message = mocks.command(None, 'general', f"emote {custom_emoji}beep{custom_emoji}")
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_b::hex_e::hex_e::hex_p:')

    @cog(EmoteCog)
    async def test_generator_converts_input_to_lower_case(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote BEEP')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_b::hex_e::hex_e::hex_p:')

    @cog(EmoteCog)
    async def test_two_consecutive_colons_are_converted_to_a_single_emoji(self, mocks: Mocks):
        message = mocks.command(None, 'general', 'emote :::')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_dc:')

        message = mocks.command(None, 'general', 'emote :::')
        await self.assert_command_successful(message)

        mocks.get_bot().context.send.assert_called_once_with('> :hex_dc:')
