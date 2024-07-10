import unittest
from test.mocks import Mocks

mocks = Mocks()


class TestTogglePermissions(unittest.IsolatedAsyncioTestCase):
    '''
    The Drone.allows_configuration_by function...
    '''

    def setUp(self):
        self.hive_mxtress = mocks.hive_mxtress()
        self.trusted_member = mocks.drone_member('5678')
        self.member = mocks.drone_member('1234', drone_trusted_users=[self.trusted_member.id])
        self.untrusted_member = mocks.drone_member('9999')

    async def test_mxtress_can_toggle(self):
        '''
        Should return true if the toggling user is Hive Mxtress.
        '''

        self.assertTrue(self.member.drone.allows_configuration_by(self.hive_mxtress))

    async def test_trusted_users_can_toggle(self):
        '''
        Should return true if the toggling user is trusted by the toggled user.
        '''

        self.assertTrue(self.member.drone.allows_configuration_by(self.trusted_member))

    async def test_self_can_toggle_if_not_otherwise_controlled(self):
        '''
        Should return true if the toggling user is the toggled user and no one else has toggled anything.
        '''

        self.member.drone.can_self_configure = True
        self.assertTrue(self.member.drone.allows_configuration_by(self.member))

    async def test_self_cannot_toggle_if_otherwise_controlled(self):
        '''
        Should return false if the toggling user is the toggled user and someone else has toggled something.
        '''

        self.member.drone.can_self_configure = False
        self.assertFalse(self.member.drone.allows_configuration_by(self.member))

    async def test_randoms_cannot_toggle(self):
        '''
        Should return false if the toggling user is not Hive Mxtress, a trusted user, or the toggled user.
        '''

        self.assertFalse(self.member.drone.allows_configuration_by(self.untrusted_member))
