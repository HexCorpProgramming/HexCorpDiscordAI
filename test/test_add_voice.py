import unittest
from src.ai.add_voice import AddVoiceCog, NOT_A_MEMBER, ACCESS_DENIED, ACCESS_ALREADY_GRANTED, ACCESS_GRANTED
from datetime import datetime, timedelta, timezone
from src.roles import VOICE
from test.cog import cog
from test.mocks import Mocks


class AddVoiceTest(unittest.IsolatedAsyncioTestCase):

    @cog(AddVoiceCog)
    async def test_not_long_enough(self, mocks: Mocks):
        member = mocks.member('a', joined_at=datetime.now(timezone.utc) - timedelta(weeks=1))
        message = mocks.direct_command(member, 'request_voice_role')

        await self.assert_command_successful(message)

        member.add_roles.assert_not_called()
        message.channel.send.assert_called_once_with(ACCESS_DENIED)

    @cog(AddVoiceCog)
    async def test_already_granted(self, mocks: Mocks):
        member = mocks.member('a', joined_at=datetime.now(timezone.utc) - timedelta(weeks=13), roles=[VOICE])
        message = mocks.direct_command(member, 'request_voice_role')

        await self.assert_command_successful(message)

        member.add_roles.assert_not_called()
        message.channel.send.assert_called_once_with(ACCESS_ALREADY_GRANTED)

    @cog(AddVoiceCog)
    async def test_granted(self, mocks: Mocks):
        member = mocks.member('a', joined_at=datetime.now(timezone.utc) - timedelta(weeks=13))
        message = mocks.direct_command(member, 'request_voice_role')

        await self.assert_command_successful(message)

        member.add_roles.assert_called_once_with(mocks.role(VOICE))
        message.channel.send.assert_called_once_with(ACCESS_GRANTED)

    @cog(AddVoiceCog)
    async def test_not_a_member(self, mocks: Mocks):
        member = mocks.member('a', joined_at=datetime.now(timezone.utc) - timedelta(weeks=13))
        message = mocks.direct_command(member, 'request_voice_role')

        # Remove the member from the guild.
        mocks.get_guild()._members = []

        await self.assert_command_successful(message)

        member.add_roles.assert_not_called()
        message.channel.send.assert_called_once_with(NOT_A_MEMBER)
