import unittest
from unittest.mock import AsyncMock, patch

from src.ai.drone_configuration import can_toggle_permissions_for

from src.resources import HIVE_MXTRESS_USER_ID


class TestTogglePermissions(unittest.IsolatedAsyncioTestCase):
    '''
    The can_toggle_permissions_for function...
    '''

    def setUp(self):
        self.hive_mxtress = AsyncMock()
        self.hive_mxtress.id = HIVE_MXTRESS_USER_ID
        self.hive_mxtress.display_name = "Hive Mxtress"

        self.drone_member = AsyncMock()
        self.drone_member.id = "7214376142"
        self.drone_member.display_name = "⬡-Drone #3287"

        self.trusted_user_member = AsyncMock()
        self.trusted_user_member.id = "872635821"
        self.trusted_user_member.display_name = "⬡-Drone #9813"

        self.random_user_member = AsyncMock()
        self.random_user_member.id = "123456789"
        self.random_user_member.display_name = "random"

        self.get_trusted_users_patch = patch('src.ai.drone_configuration.get_trusted_users')
        self.get_trusted_users = self.get_trusted_users_patch.start()
        self.get_trusted_users.return_value = [HIVE_MXTRESS_USER_ID, self.trusted_user_member.id]

    def tearDown(self):
        self.get_trusted_users_patch.stop()

    def test_mxtress_can_toggle(self):
        '''
        should return true if the toggling user is Hive Mxtress.
        '''
        self.assertTrue(can_toggle_permissions_for(self.hive_mxtress, self.drone_member))

    def test_trusted_users_can_toggle(self):
        '''
        should return true if the toggling user is trusted by the toggled user.
        '''
        self.assertTrue(can_toggle_permissions_for(self.trusted_user_member, self.drone_member))

    @patch("src.ai.drone_configuration.can_self_configure", return_value=True)
    def test_self_can_toggle_if_not_otherwise_controlled(self, can_self_configure):
        '''
        should return true if the toggling user is the toggled user and no one else has toggled anything.
        '''
        self.assertTrue(can_toggle_permissions_for(self.drone_member, self.drone_member))

    @patch("src.ai.drone_configuration.can_self_configure", return_value=False)
    def test_self_cannot_toggle_if_otherwise_controlled(self, can_self_configure):
        '''
        should return false if the toggling user is the toggled user and someone else has toggled something.
        '''
        self.assertFalse(can_toggle_permissions_for(self.drone_member, self.drone_member))

    def test_randoms_cannot_toggle(self):
        '''
        should return false if the toggling user is not Hive Mxtress, a trusted user, or the toggled user.
        '''
        self.assertFalse(can_toggle_permissions_for(self.random_user_member, self.drone_member))
