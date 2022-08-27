import unittest
import ai.add_voice as add_voice
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta, timezone
from roles import VOICE


voice_role = Mock()
voice_role.name = VOICE


class AddVoiceTest(unittest.IsolatedAsyncioTestCase):

    async def test_not_long_enough(self):
        # setup
        context = AsyncMock()
        context.message.author.id = 1234

        member = AsyncMock()
        member.id = 1234
        member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=1)
        member.roles = []

        guild = Mock()
        guild.roles = [voice_role]
        guild.get_member.return_value = member

        # run
        await add_voice.add_voice(context, guild)

        # assert
        guild.get_member.assert_called_once_with(member.id)
        member.add_roles.assert_not_called()
        context.channel.send.assert_called_once_with(add_voice.ACCESS_DENIED)

    async def test_already_granted(self):
        # setup
        context = AsyncMock()
        context.message.author.id = 1234

        member = AsyncMock()
        member.id = 1234
        member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=13)
        member.roles = [voice_role]

        guild = Mock()
        guild.roles = [voice_role]
        guild.get_member.return_value = member

        # run
        await add_voice.add_voice(context, guild)

        # assert
        guild.get_member.assert_called_once_with(member.id)
        member.add_roles.assert_not_called()
        context.channel.send.assert_called_once_with(add_voice.ACCESS_ALREADY_GRANTED)

    async def test_granted(self):
        # setup
        context = AsyncMock()
        context.message.author.id = 1234

        member = AsyncMock()
        member.id = 1234
        member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=13)
        member.roles = []

        guild = Mock()
        guild.roles = [voice_role]
        guild.get_member.return_value = member

        # run
        await add_voice.add_voice(context, guild)

        # assert
        guild.get_member.assert_called_once_with(member.id)
        context.channel.send.assert_called_once_with(add_voice.ACCESS_GRANTED)
        member.add_roles.assert_called_once_with(voice_role)

    async def test_not_a_member(self):
        # setup
        context = AsyncMock()
        context.message.author.id = 1234

        member = AsyncMock()
        member.id = 1234
        member.joined_at = datetime.now(timezone.utc) - timedelta(weeks=13)
        member.roles = []

        guild = Mock()
        guild.roles = [voice_role]
        guild.get_member.return_value = None

        # run
        await add_voice.add_voice(context, guild)

        # assert
        guild.get_member.assert_called_once_with(member.id)
        member.add_roles.assert_not_called()
        context.channel.send.assert_called_once_with(add_voice.NOT_A_MEMBER)
