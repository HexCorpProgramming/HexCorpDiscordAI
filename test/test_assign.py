import unittest
from unittest.mock import PropertyMock
import ai.assign as assign

test_message = PropertyMock()


class AssignmentTest5(unittest.TestCase):

    def test_request_reject(self):
        test_message.content = "Beep Boop want to be drone!"
        self.assertTrue(assign.check_for_assignment_message(test_message))
