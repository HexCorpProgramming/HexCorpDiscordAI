import unittest
from unittest.mock import AsyncMock, patch, Mock, call

import roles
import ai.drone_management as drone_management


hive_mxtress_role = Mock()
hive_mxtress_role.name = roles.HIVE_MXTRESS


class DroneManagementTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        pass

    @patch("ai.drone_management.rename_drone_in_db")
    @patch("ai.drone_management.fetch_drone_with_drone_id")
    async def test_rename_drone(self, fetch_drone_with_drone_id, rename_drone_in_db):
        # setup
        old_id = "1234"
        new_id = "4312"

        drone = Mock()
        drone.id = '1234snowflake'

        member = AsyncMock()

        context = AsyncMock()
        context.guild.get_member = Mock(return_value=member)

        fetch_drone_with_drone_id.side_effect = [None, drone]

        # run
        await drone_management.rename_drone(context, old_id, new_id)

        # assert
        fetch_drone_with_drone_id.assert_has_calls([call(new_id), call(old_id)])
        context.guild.get_member.assert_called_once_with(drone.id)
        rename_drone_in_db.assert_called_once_with(old_id, new_id)
        context.send.assert_called_once_with(f"Successfully renamed drone {old_id} to {new_id}.")

    @patch("ai.drone_management.rename_drone_in_db")
    @patch("ai.drone_management.fetch_drone_with_drone_id")
    async def test_rename_drone_already_used(self, fetch_drone_with_drone_id, rename_drone_in_db):
        # setup
        old_id = "1234"
        new_id = "4312"

        drone = Mock()
        drone.id = '1234snowflake'

        colliding_drone = Mock()

        member = AsyncMock()

        context = AsyncMock()
        context.guild.get_member = Mock(return_value=member)

        fetch_drone_with_drone_id.side_effect = [colliding_drone, drone]

        # run
        await drone_management.rename_drone(context, old_id, new_id)

        # assert
        fetch_drone_with_drone_id.assert_called_once_with(new_id)
        rename_drone_in_db.assert_not_called()
        context.send.assert_called_once_with(f"ID {new_id} already in use.")

    @patch("ai.drone_management.remove_drone_from_db")
    @patch("ai.drone_management.fetch_drone_with_id")
    async def test_unassign_drone(self, fetch_drone_with_id, remove_drone_from_db):
        # setup
        drone = AsyncMock()
        drone.drone_id = '1234'

        member = AsyncMock()
        member.id = 2647623845

        guild = AsyncMock()
        guild.get_member = Mock(return_value=member)

        context = AsyncMock()
        context.bot.guilds = [guild]
        context.author.id = member.id

        fetch_drone_with_id.return_value = drone

        # run
        await drone_management.unassign_drone(context)

        # assert
        guild.get_member.assert_called_once_with(context.author.id)
        fetch_drone_with_id.assert_called_once_with(context.author.id)
        remove_drone_from_db.assert_called_once_with(drone.drone_id)
        context.send.assert_called_once_with(f"Drone with ID {drone.drone_id} unassigned.")

    @patch("ai.drone_management.remove_drone_from_db")
    @patch("ai.drone_management.fetch_drone_with_id")
    async def test_unassign_drone_does_not_exist(self, fetch_drone_with_id, remove_drone_from_db):
        # setup
        drone = AsyncMock()
        drone.drone_id = '1234'

        drone = Mock()
        drone.id = '1234snowflake'

        member = AsyncMock()
        member.id = 2647623845

        guild = AsyncMock()
        guild.get_member = Mock(return_value=member)

        context = AsyncMock()
        context.bot.guilds = [guild]
        context.author.id = member.id

        fetch_drone_with_id.return_value = None

        # run
        await drone_management.unassign_drone(context)

        # assert
        fetch_drone_with_id.assert_called_once_with(context.author.id)
        remove_drone_from_db.assert_not_called()
        context.send.assert_called_once_with('You are not a drone. Can not unassign.')

    @patch("ai.drone_management.delete_drone_order_by_drone_id")
    @patch("ai.drone_management.delete_storage_by_target_id")
    @patch("ai.drone_management.delete_drone_by_drone_id")
    def test_remove_drone_from_db(self, delete_drone_by_drone_id, delete_storage_by_target_id, delete_drone_order_by_drone_id):
        # setup
        to_remove = "1234"

        # run
        drone_management.remove_drone_from_db(to_remove)

        # assert
        delete_drone_by_drone_id.assert_called_once_with(to_remove)
        delete_storage_by_target_id.assert_called_once_with(to_remove)
        delete_drone_order_by_drone_id.assert_called_once_with(to_remove)
