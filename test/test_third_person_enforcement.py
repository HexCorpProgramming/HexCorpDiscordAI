from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch
from src.ai.third_person_enforcement import enforce_third_person, replace_third_person
from test.mocks import Mocks
from src.channels import CASUAL_CHANNEL

mocks = Mocks()


class ThirdPersonEnforcementTest(IsolatedAsyncioTestCase):

    @patch('src.ai.third_person_enforcement.DroneMember')
    async def send(self, msg: str, enforcement: bool, DroneMember: MagicMock) -> None:
        author = mocks.drone_member('1234', drone_third_person_enforcement=enforcement)
        DroneMember.create = AsyncMock(return_value=author)
        self.message = mocks.message(author, CASUAL_CHANNEL, msg)
        self.message_copy = mocks.message(author, CASUAL_CHANNEL, msg)

        await enforce_third_person(self.message, self.message_copy)

    async def test_replace_third_person(self) -> None:
        '''
        Ensure that first person pronouns are replaced correctly.
        '''

        cases = [
            ('', ''),
            ('hello world', 'hello world'),
            ('I am a drone', 'It is a drone'),
            ('a drone am I', 'a drone is it'),
            ('I am Drone.  I am Drone.', 'It is Drone.  It is Drone.'),
            ('i am i', 'It is it'),
            ('I am just me', 'It is just it'),
            ('I am by myself', 'It is by itself'),
            ('Me, myself and I', 'It, itself and it'),
            ('That is mine', 'That is its'),
            ('I\'ve got mine', 'It\'s got its'),
            ('Myself and myself or my', 'Itself and itself or its'),
            ('test! I. I? I@ I', 'test! It. It? It@ it'),
            ('I.I.I', 'It.It.It'),
            ('I. I. I', 'It. It. It'),
            ('i i i i', 'It it it it'),
            ('I\'d do what i\'d do', 'It\'d do what it\'d do'),

            # These cases could be improved.
            ('Do I just do what I like?', 'Do it just do what it like?'),
            ('I have to, have I?', 'It have to, have it?'),
        ]

        for text, expected in cases:
            self.assertEqual(replace_third_person(text), expected)

    async def test_enforce_third_person(self) -> None:
        '''
        Ensure that messages are altered if enforcement is enabled.
        '''

        await self.send('I am a drone', True)
        self.assertEqual('It is a drone', self.message_copy.content)

    async def test_enforce_third_person_off(self) -> None:
        '''
        Ensure that messages are not altered if enforcement is disabled.
        '''

        await self.send('I am a drone', False)
        self.assertEqual('I am a drone', self.message_copy.content)
