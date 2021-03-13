import unittest
from unittest.mock import AsyncMock, patch, Mock
from ai.speech_optimization import StatusType, get_status_type, status_code_regex, build_status_message, optimize_speech
from ai.data_objects import MessageCopy


class TestSpeechOptimization(unittest.IsolatedAsyncioTestCase):
    '''
    The optimize_speech function...
    '''

    @patch("ai.speech_optimization.get_status_type", return_value=(StatusType.PLAIN, Mock(), Mock()))
    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_calls_get_status_type(self, is_drone, get_status_type):
        '''
        should call 'get_status_type' if author is drone, message IDs match, and the message is a status code.
        '''
        message = AsyncMock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "5890 :: 200"

        self.assertTrue(await optimize_speech(message, message_copy))
        get_status_type.assert_called_once()

    @patch("ai.speech_optimization.build_status_message")
    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_calls_build_status_message(self, is_drone, build_status_message):
        message = Mock()
        message.author.display_name = "5890"
        message_copy = Mock()
        message_copy.content = "5890 :: 200"

        self.assertFalse(await optimize_speech(message, message_copy))
        build_status_message.assert_called_once()

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_delete_mismatching_id_messages(self, is_drone):
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

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_status_codes_transform_message_copy(self, is_drone):
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

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_plain_code(self, is_drn):
        '''
        should take a plain status code and set message copy content to plain status message.
        '''

        message = Mock()
        message.content = "5890 :: 200"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative.", message_copy.content)

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_informative_code(self, is_drn):
        '''
        should take an informative status code and set message copy content to an informative status message.
        '''

        message = Mock()
        message.content = "5890 :: 200 :: Additional information"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `200` :: Response :: Affirmative. :: Additional information", message_copy.content)

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_informative_id_code(self, is_drn):
        '''
        should take an informative address by ID and set message copy content to an equivalent translated message.
        '''

        message = Mock()
        message.content = "5890 :: 110 :: 9813 :: Hello there"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `110` :: Addressing: Drone #9813 :: Hello there", message_copy.content)

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_plain_id_code(self, is_drn):
        '''
        should take a plain address by ID and set message copy content to an address by ID message.
        '''

        message = Mock()
        message.content = "5890 :: 110 :: 9813"
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: Code `110` :: Addressing: Drone #9813", message_copy.content)

    @patch("ai.speech_optimization.is_drone", return_value=True)
    async def test_no_status_found(self, is_drn):
        '''
        should not edit the message copy if no status code is found.
        '''

        message = Mock()
        message.content = "5890 :: It is a good day to be a good drone."
        message.author.display_name = "5890"
        message_copy = MessageCopy(content=message.content)

        await optimize_speech(message, message_copy)

        self.assertEqual("5890 :: It is a good day to be a good drone.", message_copy.content)


class TestGetStatusType(unittest.TestCase):
    '''
    The get_status_type function...
    '''

    def test_returns_none_if_none(self):
        '''
        returns NONE if status is None.
        '''
        status_type, _, _ = get_status_type("hewwo!!!")
        self.assertEqual(StatusType.NONE, status_type)

    def test_returns_informative_if_informative_text(self):
        '''
        returns INFORMATIVE if status has informative text group.
        '''
        status_type, _, _ = get_status_type("5890 :: 050 :: It is a good drone.")
        self.assertEqual(StatusType.INFORMATIVE, status_type)

    def test_returns_informative_if_addr_regex_doesnt_match(self):
        '''
        returns INFORMATIVE if 110 status does not match addressing information regex.
        '''
        status_type, _, _ = get_status_type("5890 :: 110 :: Hello there, General kedroney.")
        self.assertEqual(StatusType.INFORMATIVE, status_type)

    def test_returns_addr_by_id_info_if_addr_has_informative(self):
        '''
        returns ADDRESS_BY_ID_INFORMATIVE if 110 status matches addressing info regex and has informative text
        '''
        status_type, _, _ = get_status_type("5890 :: 110 :: 9813 :: How are you today?")
        self.assertEqual(StatusType.ADDRESS_BY_ID_INFORMATIVE, status_type)

    def test_returns_addr_by_id_plain_if_no_informative(self):
        '''
        returns ADDRESS_BY_ID_PLAIN if 110 status matches extra regex and has no informative text
        '''
        status_type, _, _ = get_status_type("5890 :: 110 :: 9813")
        self.assertEqual(StatusType.ADDRESS_BY_ID_PLAIN, status_type)

    def test_returns_plain_if_no_informative_text(self):
        '''
        returns PLAIN if code has no informative text
        '''
        status_type, _, _ = get_status_type("5890 :: 304")
        self.assertEqual(StatusType.PLAIN, status_type)


class TestBuildStatusMessage(unittest.TestCase):
    '''
    The build_status_message function...
    '''

    def test_plain_message(self):
        '''
        returns a plain status message when given a plain status code.
        '''

        status_type, code_match, address_match = get_status_type("5890 :: 200")

        self.assertEqual(
            "5890 :: Code `200` :: Response :: Affirmative.",
            build_status_message(status_type, code_match, address_match)
        )

    def test_informative_message(self):
        '''
        returns an informative status message when given an informative status code.
        '''

        status_type, code_match, address_match = get_status_type("5890 :: 050 :: Goodbye.")

        self.assertEqual(
            "5890 :: Code `050` :: Statement :: Goodbye.",
            build_status_message(status_type, code_match, address_match)
        )

    def test_plain_address_message(self):
        '''
        returns a plain address by ID status message when a 110 code references a drone by ID.
        '''

        status_type, code_match, address_match = get_status_type("5890 :: 110 :: 9813")

        self.assertEqual(
            "5890 :: Code `110` :: Addressing: Drone #9813",
            build_status_message(status_type, code_match, address_match)        
        )

    def test_informative_address_message(self):
        '''
        returns an informative address by ID status message when a 110 code references a drone by ID with additional information.
        '''

        status_type, code_match, address_match = get_status_type("5890 :: 110 :: 9813 :: Hello.")

        self.assertEqual(
            "5890 :: Code `110` :: Addressing: Drone #9813 :: Hello.",
            build_status_message(status_type, code_match, address_match)        
        )
