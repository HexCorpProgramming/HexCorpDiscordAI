import unittest
from unittest.mock import patch, Mock

from src.db.maintenance import trusted_user_cleanup


class MaintenanceTest(unittest.IsolatedAsyncioTestCase):

    @patch("src.db.maintenance.set_trusted_users")
    @patch("src.db.maintenance.get_all_drones")
    async def test_trusted_user_cleanup(self, get_all_drones, set_trusted_users):
        # init
        drone_with_dangling_users = Mock()
        drone_with_dangling_users.trusted_users = "1|2"
        drone_with_dangling_users.id = 3
        drone_with_no_dangling_users = Mock()
        drone_with_no_dangling_users.trusted_users = "1"
        drone_with_no_dangling_users.id = 4
        drones = [drone_with_dangling_users, drone_with_no_dangling_users]

        get_all_drones.return_value = drones

        associate = Mock()
        associate.id = 1
        members = [associate]

        # run
        await trusted_user_cleanup(members)

        # assert
        set_trusted_users.assert_called_once_with(3, [1])
