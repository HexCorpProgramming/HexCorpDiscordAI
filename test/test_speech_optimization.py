import unittest
from unittest.mock import AsyncMock, patch, Mock

import roles
import channels
import ai.speech_optimization as speech_optimization

from ai.data_objects import MessageCopy

from ai.speech_optimization import StatusType, get_status_type, status_code_regex
import re

drone_role = Mock()
drone_role.name = roles.DRONE

optimized_role = Mock()
optimized_role.name = roles.SPEECH_OPTIMIZATION

class SpeechOptimizationTest(unittest.IsolatedAsyncioTestCase):
    '''
    should_not_optimize:
        - returns True if channel is repetitions and message content is mantra
        - acceptable mantra includes a drone's ID.
        - returns True if channel category is moderation channel
        - returns True if channel name in whitelist
        - returns False otherwise

    build_status_message:
        - should return an appropriate message for:
        - PLAIN
        - INFORMATIVE
        - ADDRESS_BY_ID_PLAIN
        - ADDRESS_BY_ID_INFORMATIVE
        - should return None if NONE.

    optimize_speech:
        - should call:
        - should_not_optimize
        - get_status_type
        - build_status_message
        - discards messages if the status ID does not match drone ID
    '''


class GetStatusTypeTest(unittest.TestCase):
    '''
    The get_status_type function...
    '''

    def test_returns_none_if_none(self):
        '''
        returns NONE if status is None.
        '''
        message = status_code_regex.match("hewwo!!!!!!!")
        self.assertEqual(StatusType.NONE, get_status_type(message))

    def test_returns_informative_if_informative_text(self):
        '''
        returns INFORMATIVE if status has informative text group.
        '''
        message = status_code_regex.match("5890 :: 050 :: It is a good drone.")
        self.assertEqual(StatusType.INFORMATIVE, get_status_type(message))

    def test_returns_informative_if_addr_regex_doesnt_match(self):
        '''
        returns INFORMATIVE if 110 status does not match addressing information regex.
        '''
        message = status_code_regex.match("5890 :: 110 :: Hello there droney.")
        self.assertEqual(StatusType.INFORMATIVE, get_status_type(message))

    def test_returns_addr_by_id_info_if_addr_has_informative(self):
        '''
        returns ADDRESS_BY_ID_INFORMATIVE if 110 status matches addressing info regex and has informative text
        '''
        message = status_code_regex.match("5890 :: 110 :: 9813 :: How are you today?")
        self.assertEqual(StatusType.ADDRESS_BY_ID_INFORMATIVE, get_status_type(message))

    def test_returns_addr_by_id_plain_if_no_informative(self):
        '''
        returns ADDRESS_BY_ID_PLAIN if 110 status matches extra regex and has no informative text
        '''
        message = status_code_regex.match("5890 :: 110 :: 9813")
        self.assertEqual(StatusType.ADDRESS_BY_ID_PLAIN, get_status_type(message))

    def test_returns_plain_if_no_informative_text(self):
        '''
        returns PLAIN if code has no informative text
        '''
        message = status_code_regex.match("5890 :: 304")
        self.assertEqual(StatusType.PLAIN, get_status_type(message))


class ShouldNotOptimizeTest(unittest.TestCase):
    '''
    The should_not_optimize function...
    '''

    def test_true_if_mantra_in_mantra_channel(self):
        '''
        returns true if message channel is repetitions and message content is correct mantra.
        '''
        return True

    def test_manta_string_contains_authors_drone_id(self):
        '''
        should generate a mantra check string using the author's drone ID.
        '''
        return True

    def test_true_if_channel_name_in_whitelist(self):
        '''
        returns true if message channel name is in whitelist.
        '''
        return True

    def test_true_if_channel_category_is_moderation(self):
        '''
        returns true if channel category name is in whitelist.
        '''
        return True

    def test_false_otherwise(self):
        '''
        returns false if none of the above.
        '''
        return True
