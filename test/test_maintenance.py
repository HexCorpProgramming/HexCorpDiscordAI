import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.db.maintenance import trusted_user_cleanup
from test.mocks import Mocks

mocks = Mocks()


class MaintenanceTest(unittest.IsolatedAsyncioTestCase):

    @patch("src.db.maintenance.Drone")
    async def test_trusted_user_cleanup(self, Drone: MagicMock):
        # init
        drone_with_dangling_users = mocks.drone(1234, trusted_users=[1, 2])
        drone_with_no_dangling_users = mocks.drone(5678, trusted_users=[1])
        drones = [drone_with_dangling_users, drone_with_no_dangling_users]

        Drone.all = AsyncMock(return_value=drones)

        members = [mocks.member(id=1)]

        # run
        await trusted_user_cleanup(members)

        # assert
        self.assertEqual(drone_with_dangling_users.trusted_users, [1])
        drone_with_dangling_users.save.assert_called_once()

        self.assertEqual(drone_with_no_dangling_users.trusted_users, [1])
        drone_with_no_dangling_users.save.assert_not_called()
