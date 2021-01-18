import unittest
from unittest.mock import AsyncMock, patch, Mock

import roles
import channels
import ai.speech_optimization as speech_optimization

from ai.data_objects import MessageCopy

drone_role = Mock()
drone_role.name = roles.DRONE

optimized_role = Mock()
optimized_role.name = roles.SPEECH_OPTIMIZATION


class SpeechOptimizationTest(unittest.IsolatedAsyncioTestCase):
    '''
    should_not_optimize:
        - returns True if channel is repetitions and message content is mantra
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
    '''


class GetStatusTypeTest(unittest.TestCase):

    def returns_none_if_none():
        '''
        returns NONE if status is None.
        '''

    def returns_informative_if_informative_text():
        '''
        returns INFORMATIVE if status has informative text group.
        '''

    def returns_informative_if_addr_regex_doesnt_match():
        '''
        returns INFORMATIVE if 110 status does not match addressing information regex.
        '''

    def returns_addr_by_id_info_if_addr_has_informative():
        '''
        returns ADDRESS_BY_ID_INFORMATIVE if 110 status matches addressing info regex and has informative text
        '''

    def returns_addr_by_id_plain_if_no_informative():
        '''
        returns ADDRESS_BY_ID_PLAIN if 110 status matches extra regex and has no informative text
        '''

    def returns_plain_if_no_informative_text():
        '''
        returns PLAIN if code has no informative text
        '''