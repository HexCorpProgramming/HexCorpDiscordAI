import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai.forbidden_word import deny_thoughts
from src.db.data_objects import ForbiddenWord
from test.mocks import Mocks

mocks = Mocks()


class ThoughtDenialTest(unittest.IsolatedAsyncioTestCase):

    author: MagicMock
    message: MagicMock

    @patch('src.ai.forbidden_word.ForbiddenWord')
    @patch('src.ai.forbidden_word.DroneMember')
    async def deny(self, msg: str, expected: str, DroneMember: MagicMock, ForbiddenWords: MagicMock) -> None:
        self.author = mocks.drone_member('1234')
        message = mocks.message(self.author, '', msg)
        message_copy = mocks.message(self.author, '', msg)

        ForbiddenWords.all = AsyncMock(return_value=[ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")])
        DroneMember.create = AsyncMock(return_value=self.author)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, expected)

    async def test_remove_short_thought_from_message(self) -> None:
        '''
        deny_thoughts should replace the word 'thoughts' with '\_\_\_\_\_\_\_s'. If the user is a drone.
        The backslashes are to escape Discord's formatting. Double underscores are used for underlining in Discord.
        '''

        await self.deny('I love to have thoughts.', r'I love to have \_\_\_\_\_\_\_s.')

    async def test_remove_long_thought_from_message(self) -> None:
        '''
        deny_thoughts should replace 'thouuuugghhhhtttts' with '\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_s'. If the user is a drone.
        Regex should be able to match any number of drawn out characters, so long as 'thought' is still spelled correctly.
        '''

        await self.deny('I love to have thouuuugghhhhtttts.', r'I love to have \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_s.')

    async def test_remove_short_think_from_message(self) -> None:
        '''
        deny_thoughts should replace the word 'think' with '\_\_\_\_\_' if the user is a drone.
        '''

        await self.deny('I love to think.', r'I love to \_\_\_\_\_.')

    async def test_remove_long_think_from_message(self) -> None:
        '''
        deny_thoughts should replace 'thiiiiiiiiinkkkk' with '\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_' if the user is a drone.
        Regex should be able to match any number of drawn out characters, so long as 'think' is still spelled correctly.
        '''

        await self.deny('I love to thiiiiiiiiinkkkk.', r'I love to \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_.')

    @patch('src.ai.forbidden_word.DroneMember')
    async def test_forbidden_word_ignores_non_drones(self, DroneMember: MagicMock):
        '''
        The thought denial module should have no effect on the messages of any non-drone (associate or Hive Mxtress).
        '''

        self.author = mocks.drone_member('1234', drone=None)
        msg = 'I am an associate. I love to think about my free will and I have thoughts about drones.'
        message = mocks.message(self.author, '', msg)
        message_copy = mocks.message(self.author, '', msg)

        DroneMember.create = AsyncMock(return_value=self.author)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message.content, message_copy.content)

    async def test_replace_thinking_emoji_with_custom(self) -> None:
        '''
        deny_thoughts should replace all instances of the thinking emoji (🤔) in a drone's message with the custom :programmedHexDrone: emoji.
        '''

        await self.deny('Hmmm... 🤔', 'Hmmm... :hexdroneemoji:')
