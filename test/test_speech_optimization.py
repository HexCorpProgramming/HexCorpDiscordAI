import unittest
from unittest.mock import AsyncMock, patch, Mock
from channels import REPETITIONS, ORDERS_REPORTING, ORDERS_COMPLETION, MODERATION_CHANNEL, MODERATION_LOG, MODERATION_CATEGORY
from ai.speech_optimization import StatusType, get_status_type, status_code_regex, should_not_optimize, build_status_message, optimize_speech
from ai.data_objects import MessageCopy

class TestSpeechOptimization(unittest.IsolatedAsyncioTestCase):
    '''
    The optimize_speech function...
    '''

    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.should_not_optimize")
    async def test_calls_should_not_optimize(self, should_not_optimize, is_drone):
        '''
        should call 'should_not_optimize' once if message author is a drone.
        '''
        message = Mock()
        message_copy = Mock()
        self.assertFalse(await optimize_speech(message, message_copy))
        should_not_optimize.assert_called_once()

    @patch("ai.speech_optimization.get_status_type")
    @patch("ai.speech_optimization.is_optimized", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    async def test_calls_get_status_type(self, should_not_optimize, is_drone, is_optimized, get_status_type):
        '''
        should call 'get_status_type' if author is drone, message IDs match, and the message is a status code.
        '''
        message = Mock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "5890 :: 200"

        self.assertFalse(await optimize_speech(message, message_copy))
        get_status_type.assert_called_once()

    @patch("ai.speech_optimization.build_status_message")
    @patch("ai.speech_optimization.is_optimized", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    async def test_calls_build_status_message(self, should_not_optimize, is_drone, is_optimized, build_status_message):
        message = Mock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "5890 :: 200"

        self.assertFalse(await optimize_speech(message, message_copy))
        build_status_message.assert_called_once()

    @patch("ai.speech_optimization.is_optimized", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    async def test_delete_mismatching_id_messages(self, should_not_optimize, is_drone, is_optimized):
        '''
        should delete message if author ID does not match status ID.
        '''
        message = AsyncMock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "9813 :: 200"

        self.assertTrue(await optimize_speech(message, message_copy))
        message.delete.assert_called_once()

    @patch("ai.speech_optimization.is_drone", return_value=False)
    async def test_dont_operate_on_non_drone_messages(self, is_drone):
        '''
        should return False early if message author is not a drone.
        '''
        message = Mock()
        message_copy = Mock()
        self.assertFalse(await optimize_speech(message, message_copy))

    @patch("ai.speech_optimization.is_optimized", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    async def test_status_codes_transform_message_copy(self, should_not_optimize, is_drone, is_optimized):
        '''
        should update message_copy when passed message content with a valid status code.
        '''
        message = AsyncMock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "5890 :: 200"

        self.assertFalse(await optimize_speech(message, message_copy))
        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative.", message_copy.content)

        message_copy.content = "5890 :: 200 :: Additional information."

        self.assertFalse(await optimize_speech(message, message_copy))
        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative. :: Additional information.", message_copy.content)

    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.is_optimized", return_value=True)
    async def test_attachments_removed(self, is_op, is_drn, not_op):
        '''
        should remove attachments from message_copy if drone is optimized.
        '''

        message = Mock()
        message.content = "5890 :: 200"
        message.author.display_name = "5890"

        message_copy = MessageCopy()
        message_copy.attachments = ["attachment1", "attachment2", "so on and so forth."]
        message_copy.content = "5890 :: 200"

        await optimize_speech(message, message_copy)

        self.assertEqual([], message_copy.attachments)

    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.is_optimized", return_value=True)
    async def test_plain_code(self, is_op, is_drn, not_op):
        '''
        should take a plain status code and set message copy content to plain status message.
        '''

        message = Mock()
        message.content = "5890 :: 200"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative.", message_copy.content)

    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.is_optimized", return_value=False)
    async def test_informative_code(self, is_op, is_drn, not_op):
        '''
        should take an informative status code and set message copy content to an informative status message.
        '''

        message = Mock()
        message.content = "5890 :: 200 :: Additional information"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative. :: Additional information", message_copy.content)

    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.is_optimized", return_value=False)
    async def test_informative_id_code(self, is_op, is_drn, not_op):
        '''
        should take an informative address by ID and set message copy content to an equivalent translated message.
        '''

        message = Mock()
        message.content = "5890 :: 110 :: 9813 :: Hello there"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `110` :: Addressing: Drone #9813 :: Hello there", message_copy.content)

    @patch("ai.speech_optimization.should_not_optimize", return_value=False)
    @patch("ai.speech_optimization.is_drone", return_value=True)
    @patch("ai.speech_optimization.is_optimized", return_value=True)
    async def test_plain_id_code(self, is_op, is_drn, not_op):
        '''
        should take a plain address by ID and set message copy content to an address by ID message.
        '''

        message = Mock()
        message.content = "5890 :: 110 :: 9813"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `110` :: Addressing: Drone #9813", message_copy.content)


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
