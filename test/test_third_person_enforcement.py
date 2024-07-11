from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch
from src.ai.third_person_enforcement import enforce_third_person, replace_third_person


class ThirdPersonEnforcementTest(IsolatedAsyncioTestCase):

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

    @patch('src.ai.third_person_enforcement.third_person_enforcable', return_value=True)
    async def test_enforce_third_person(self, third_person_enforcable) -> None:
        '''
        Ensure that messages are altered if enforcement is enabled.
        '''

        message = Mock()
        message_copy = Mock(content='I am a drone')

        await enforce_third_person(message, message_copy)

        self.assertEqual('It is a drone', message_copy.content)

    @patch('src.ai.third_person_enforcement.third_person_enforcable', return_value=False)
    async def test_enforce_third_person_off(self, third_person_enforcable) -> None:
        '''
        Ensure that messages are not altered if enforcement is disabled.
        '''

        message = Mock()
        message_copy = Mock(content='I am a drone')

        await enforce_third_person(message, message_copy)

        self.assertEqual('I am a drone', message_copy.content)
