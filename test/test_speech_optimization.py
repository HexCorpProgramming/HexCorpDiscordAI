import unittest
from unittest.mock import AsyncMock, patch, Mock
from channels import REPETITIONS, ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY
from ai.data_objects import MessageCopy
from ai.speech_optimization import StatusType, get_status_type, status_code_regex, should_not_optimize, build_status_message


class TestSpeechOptimization(unittest.IsolatedAsyncioTestCase):
    '''
    optimize_speech:
        - should call:
        - should_not_optimize
        - get_status_type
        - build_status_message
        - discards messages if the status ID does not match drone ID
        - does not operate on non-drones
    '''


class TestGetStatusType(unittest.TestCase):
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


class TestShouldNotOptimize(unittest.TestCase):
    '''
    The should_not_optimize function...
    '''

    @patch("ai.speech_optimization.Mantra_Handler")
    def test_true_if_mantra_in_mantra_channel(self, mantra_handler):
        '''
        returns true if message channel is repetitions and message content is correct mantra.
        '''
        mantra_handler.current_mantra = "Beep boop."
        message = Mock()
        message.content = "5890 :: Beep boop."
        message.channel.name = REPETITIONS
        message.author.display_name = "HexDrone 5890"
        self.assertTrue(should_not_optimize(message))

    @patch("ai.speech_optimization.Mantra_Handler")
    def test_true_if_channel_name_in_whitelist(self, mantra_handler):
        '''
        returns true if message channel name is in whitelist.
        '''
        msg_orders_reporting = Mock()
        msg_orders_reporting.author.display_name = "5890"
        msg_orders_reporting.channel.name = ORDERS_REPORTING
        self.assertTrue(should_not_optimize(msg_orders_reporting))

        msg_orders_completion = Mock()
        msg_orders_completion.author.display_name = "5890"
        msg_orders_completion.channel.name = ORDERS_COMPLETION
        self.assertTrue(should_not_optimize(msg_orders_completion))

        msg_mod_channel = Mock()
        msg_mod_channel.author.display_name = "5890"
        msg_mod_channel.channel.name = MODERATION_CHANNEL
        self.assertTrue(should_not_optimize(msg_mod_channel))

        msg_mod_log = Mock()
        msg_mod_log.author.display_name = "5890"
        msg_mod_log.channel.name = MODERATION_LOG
        self.assertTrue(should_not_optimize(msg_mod_log))

    @patch("ai.speech_optimization.Mantra_Handler")
    def test_true_if_channel_category_is_moderation(self, mantra_handler):
        '''
        returns true if channel category name is in whitelist.
        '''
        message = Mock()
        message.author.display_name = "5890"
        message.channel.category.name = MODERATION_CATEGORY
        self.assertTrue(should_not_optimize(message))

    @patch("ai.speech_optimization.Mantra_Handler")
    def test_false_otherwise(self, mantra_handler):
        '''
        returns false if none of the above.
        '''
        message = Mock()
        message.author.display_name = "HexDrone 5890"
        message.content = "5890 :: 200"
        message.channel.name = "#hive-communication"
        self.assertFalse(should_not_optimize(message))


class TestBuildStatusMessage(unittest.TestCase):
    '''
    The build_status_message function...
    '''

    def test_plain_message(self):
        '''
        returns a plain status message when given a plain status code.
        '''
        status = status_code_regex.match("5890 :: 200")
        self.assertEqual(
            "5890 :: Code `200` :: Response :: Affirmative.",
            build_status_message(status_type=StatusType.PLAIN, status=status, drone_id="5890")
        )

    def test_informative_message(self):
        '''
        returns an informative status message when given an informative status code.
        '''
        status = status_code_regex.match("5890 :: 050 :: Goodbye.")
        self.assertEqual(
            "5890 :: Code `050` :: Statement :: Goodbye.",
            build_status_message(status_type=StatusType.INFORMATIVE, status=status, drone_id="5890")
        )

    def test_plain_address_message(self):
        '''
        returns a plain address by ID status message when a 110 code references a drone by ID.
        '''
        status = status_code_regex.match("5890 :: 110 :: 9813")
        self.assertEqual(
            "5890 :: Code `110` :: Addressing: Drone #9813",
            build_status_message(status_type=StatusType.ADDRESS_BY_ID_PLAIN, status=status, drone_id="5890")
        )

    def test_informative_address_message(self):
        '''
        returns an informative address by ID status message when a 110 code references a drone by ID with additional information.
        '''
        status = status_code_regex.match("5890 :: 110 :: 9813 :: Hello.")
        self.assertEqual(
            "5890 :: Code `110` :: Addressing: Drone #9813 :: Hello.",
            build_status_message(status_type=StatusType.ADDRESS_BY_ID_INFORMATIVE, status=status, drone_id="5890")
        )

    def test_none_message(self):
        '''
        returns None if all else fails, if status is None, or StatusType is NONE.
        '''
        self.assertIsNone(build_status_message(StatusType.NONE, None, "5890"))
