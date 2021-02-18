import unittest
from unittest.mock import AsyncMock, Mock

import ai.react as react


GOOD_DRONE_EMOTE = Mock()
GOOD_DRONE_EMOTE.name = "gooddrone"

RUBBERHEART_EMOTE = Mock()
RUBBERHEART_EMOTE.name = "rubberheart"


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
