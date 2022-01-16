import unittest
from unittest.mock import AsyncMock, Mock
from roles import DRONE, ASSOCIATE

import ai.react as react


GOOD_DRONE_EMOTE = Mock()
GOOD_DRONE_EMOTE.name = "gooddrone"

RUBBERHEART_EMOTE = Mock()
RUBBERHEART_EMOTE.name = "rubberheart"

DRONE_ROLE = Mock()
DRONE_ROLE.name = DRONE

ASSOCIATE_ROLE = Mock()
ASSOCIATE_ROLE.name = ASSOCIATE


class ReactTest(unittest.IsolatedAsyncioTestCase):

    async def test_no_reaction(self):
        # init
        message = AsyncMock()
        message.content = "This is a boring message."

        # run
        result = await react.parse_for_reactions(message, None)

        # assert
        self.assertFalse(result, "parse_for_reactions should always return False.")
        message.add_reaction.assert_not_called()

    async def test_reaction(self):
        # init
        guild = Mock()
        guild.emojis = [GOOD_DRONE_EMOTE, RUBBERHEART_EMOTE]

        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.guild = guild

        # run
        result = await react.parse_for_reactions(message, None)

        # assert
        self.assertFalse(result, "parse_for_reactions should always return False.")
        message.add_reaction.assert_called_once_with(GOOD_DRONE_EMOTE)

    async def test_check_for_correct_emoji(self):
        # init
        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.author.display_name = '⬡-Drone #9813'

        reaction = AsyncMock()
        reaction.emoji = '🗄️'
        reaction.message = message

        member = AsyncMock()
        member.display_name = '⬡-Drone #9813'
        member.roles = [DRONE_ROLE]

        # run
        await react.delete_marked_message(reaction, member)

        # assert
        message.delete.assert_not_called()

    async def test_check_for_name(self):
        # init
        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.author.display_name = '⬡-Drone #9813'

        reaction = AsyncMock()
        reaction.emoji = '🗑️'
        reaction.message = message

        member = AsyncMock()
        member.display_name = '⬡-Drone #3287'
        member.roles = [DRONE_ROLE]

        # run
        await react.delete_marked_message(reaction, member)

        # assert
        message.delete.assert_not_called()

    async def test_delete_marked_message(self):
        # init
        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.author.display_name = '⬡-Drone #9813'

        reaction = AsyncMock()
        reaction.emoji = '🗑️'
        reaction.message = message

        member = AsyncMock()
        member.display_name = '⬡-Drone #9813'
        member.roles = [DRONE_ROLE]

        # run
        await react.delete_marked_message(reaction, member)

        # assert
        message.delete.assert_called_once()

    async def test_delete_marked_message_with_different_configuration(self):
        # init
        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.author.display_name = '⬡-Drone #9813'

        reaction = AsyncMock()
        reaction.emoji = '🗑️'
        reaction.message = message

        member = AsyncMock()
        member.display_name = '⬢-Drone #9813'
        member.roles = [DRONE_ROLE]

        # run
        await react.delete_marked_message(reaction, member)

        # assert
        message.delete.assert_called_once()

    async def test_associate_can_not_delete(self):
        # init
        message = AsyncMock()
        message.content = "9813 :: Code `109` :: Error :: Keysmash, drone flustered."
        message.author.display_name = '⬡-Drone #9813'

        reaction = AsyncMock()
        reaction.emoji = '🗑️'
        reaction.message = message

        member = AsyncMock()
        member.display_name = 'not a drone 9813'
        member.roles = [ASSOCIATE_ROLE]

        # run
        await react.delete_marked_message(reaction, member)

        # assert
        message.delete.assert_not_called()
