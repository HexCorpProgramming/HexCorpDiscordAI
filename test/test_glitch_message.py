import unittest
from ai.glitch_message import escape_characters, protected_text_regex


class GlitchMessageTest(unittest.TestCase):

    def test_escape_custom_emoji(self):
        # init
        message = "abcd <:custom_emoji:123456789012345678> hgjgjh"

        # run
        _, modified_message = escape_characters(message, protected_text_regex)

        # assert
        self.assertEqual(modified_message, "abcd  hgjgjh")

    def test_escape_spoiler(self):
        # init
        message = "abcd||this should not be glitched||hgjgjh"

        # run
        _, modified_message = escape_characters(message, protected_text_regex)

        # assert
        self.assertEqual(modified_message, "abcdhgjgjh")

    def test_escape_hyperlinks(self):
        # init
        message = "abcd https://www.hexcorp.net hgjgjh"

        # run
        _, modified_message = escape_characters(message, protected_text_regex)

        # assert
        self.assertEqual(modified_message, "abcd  hgjgjh")

    def test_escape_nothing(self):
        # init
        message = "abcd  hgjgjh"

        # run
        _, modified_message = escape_characters(message, protected_text_regex)

        # assert
        self.assertEqual(modified_message, "abcd  hgjgjh")

    def test_escape_all(self):
        # init
        message = "beep <:custom_emoji:123456789012345678> boop https://www.hexcorp.net beep ||this should not be glitched|| boop"

        # run
        _, modified_message = escape_characters(message, protected_text_regex)

        # assert
        self.assertEqual(modified_message, "beep  boop  beep  boop")
