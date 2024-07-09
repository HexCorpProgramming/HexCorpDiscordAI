import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ai.speech_optimization import StatusType, get_status_type, build_status_message, optimize_speech
from test.mocks import Mocks
from src.channels import CASUAL_CHANNEL

mocks = Mocks()


class TestSpeechOptimization(unittest.IsolatedAsyncioTestCase):
    '''
    The optimize_speech function...
    '''

    def setUp(self) -> None:
        self.author = mocks.drone_member('1234')

    @patch('src.ai.speech_optimization.DroneMember')
    async def send(self, msg: str, DroneMember: MagicMock) -> None:
        DroneMember.create = AsyncMock(return_value=self.author)
        self.message = mocks.message(self.author, CASUAL_CHANNEL, msg)
        self.message_copy = mocks.message(self.author, CASUAL_CHANNEL, msg)

        await optimize_speech(self.message, self.message_copy)

    async def test_delete_mismatching_id_messages(self) -> None:
        '''
        Should delete message if author ID does not match status ID.
        '''

        await self.send('5678 :: 200')
        self.message.delete.assert_called_once()

    async def test_dont_operate_on_non_drone_messages(self) -> None:
        '''
        Should not modify message author is not a drone.
        '''

        self.author.drone = None
        await self.send('1234 :: 200')

        self.assertEqual(self.message.content, self.message_copy.content)

    async def test_plain_code(self) -> None:
        '''
        Should take a plain status code and set message copy content to plain status message.
        '''

        await self.send('1234 :: 200')

        self.assertEqual(self.message_copy.content, '1234 :: Code `200` :: Response :: Affirmative.')

    async def test_informative_code(self) -> None:
        '''
        Should take an informative status code and set message copy content to an informative status message.
        '''

        await self.send('1234 :: 200 :: Additional information.')

        self.assertEqual(self.message_copy.content, '1234 :: Code `200` :: Response :: Affirmative. :: Additional information.')

    async def test_informative_id_code(self) -> None:
        '''
        Should take an informative address by ID and set message copy content to an equivalent translated message.
        '''

        await self.send('1234 :: 110 :: 9813 :: Hello there')

        self.assertEqual(self.message_copy.content, '1234 :: Code `110` :: Addressing: Drone #9813 :: Hello there')

    async def test_plain_id_code(self) -> None:
        '''
        Should take a plain address by ID and set message copy content to an address by ID message.
        '''

        await self.send('1234 :: 110 :: 9813')

        self.assertEqual(self.message_copy.content, '1234 :: Code `110` :: Addressing: Drone #9813')

    async def test_no_status_found(self) -> None:
        '''
        Should not edit the message copy if no status code is found.
        '''

        msg = '1234 :: It is a good day to be a good drone.'
        await self.send(msg)

        self.assertEqual(self.message_copy.content, msg)


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
