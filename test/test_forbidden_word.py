import unittest
from unittest.mock import patch, Mock
from src.ai.forbidden_word import deny_thoughts
from src.ai.data_objects import MessageCopy
from src.db.data_objects import ForbiddenWord


class ThoughtDenialTest(unittest.IsolatedAsyncioTestCase):

    @patch("src.ai.forbidden_word.get_all_forbidden_words")
    @patch("src.ai.forbidden_word.get")
    @patch("src.ai.forbidden_word.is_drone")
    async def test_remove_short_thought_from_message(self, is_drone, emoji_get, get_all_forbidden_words):
        """
        deny_thoughts should replace the word 'thoughts' with '\_\_\_\_\_\_\_s'. If the user is a drone.
        The backslashes are to escape Discord's formatting. Double underscores are used for underlining in Discord.
        """

        is_drone.return_value = True
        emoji_get.return_value = "Unused for this test."
        get_all_forbidden_words.return_value = [ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")]

        message = Mock()
        message.content = "I love to have thoughts."

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, "I love to have \_\_\_\_\_\_\_s.")

    @patch("src.ai.forbidden_word.get_all_forbidden_words")
    @patch("src.ai.forbidden_word.get")
    @patch("src.ai.forbidden_word.is_drone")
    async def test_remove_long_thought_from_message(self, is_drone, emoji_get, get_all_forbidden_words):
        """
        deny_thoughts should replace 'thouuuugghhhhtttts' with '\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_s'. If the user is a drone.
        Regex should be able to match any number of drawn out characters, so long as 'thought' is still spelled correctly.
        """

        is_drone.return_value = True
        emoji_get.return_value = "Unused for this test."
        get_all_forbidden_words.return_value = [ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")]

        message = Mock()
        message.content = "I love to have thouuuugghhhhtttts."

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, "I love to have \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_s.")

    @patch("src.ai.forbidden_word.get_all_forbidden_words")
    @patch("src.ai.forbidden_word.get")
    @patch("src.ai.forbidden_word.is_drone")
    async def test_remove_short_think_from_message(self, is_drone, emoji_get, get_all_forbidden_words):
        """
        deny_thoughts should replace the word 'think' with '\_\_\_\_\_' if the user is a drone.
        """

        is_drone.return_value = True
        emoji_get.return_value = "Unused for this test."
        get_all_forbidden_words.return_value = [ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")]

        message = Mock()
        message.content = "I love to think."

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, "I love to \_\_\_\_\_.")

    @patch("src.ai.forbidden_word.get_all_forbidden_words")
    @patch("src.ai.forbidden_word.get")
    @patch("src.ai.forbidden_word.is_drone")
    async def test_remove_long_think_from_message(self, is_drone, emoji_get, get_all_forbidden_words):
        """
        deny_thoughts should replace 'thiiiiiiiiinkkkk' with '\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_' if the user is a drone.
        Regex should be able to match any number of drawn out characters, so long as 'think' is still spelled correctly.
        """

        is_drone.return_value = True
        emoji_get.return_value = "Unused for this test."
        get_all_forbidden_words.return_value = [ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")]

        message = Mock()
        message.content = "I love to thiiiiiiiiinkkkk."

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, "I love to \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_.")

    @patch("src.ai.forbidden_word.is_drone")
    async def test_forbidden_word_ignores_non_drones(self, is_drone):
        """
        The thought denial module should have no effect on the messages of any non-drone (associate or Hive Mxtress).
        """

        is_drone.return_value = False

        message = Mock()
        message.content = "I am an associate. I love to think about my free will and I have thoughts about drones."

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message.content, message_copy.content)

    @patch("src.ai.forbidden_word.get_all_forbidden_words")
    @patch("src.ai.forbidden_word.get")
    @patch("src.ai.forbidden_word.is_drone")
    async def test_replace_thinking_emoji_with_custom(self, is_drone, emoji_get, get_all_forbidden_words):
        """
        deny_thoughts should replace all instances of the thinking emoji (🤔) in a drone's message with the custom :programmedHexDrone: emoji.
        """

        HexDroneemoji = Mock()

        is_drone.return_value = True
        emoji_get.return_value = HexDroneemoji
        get_all_forbidden_words.return_value = [ForbiddenWord("morning", "m+o+r+n+i+n+g+"), ForbiddenWord("think", "t+h+i+n+k+"), ForbiddenWord("thought", "t+h+o+u+g+h+t+")]

        message = Mock()
        message.content = "Hmmm... 🤔"

        message_copy = MessageCopy(message.content)

        await deny_thoughts(message, message_copy)

        self.assertEqual(message_copy.content, f"Hmmm... {str(HexDroneemoji)}")
