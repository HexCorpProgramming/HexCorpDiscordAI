import unittest
from unittest.mock import AsyncMock, patch, Mock, call

import src.roles as roles
from src.ai.drone_configuration import DroneConfigurationCog
# from src.db.drone_dao import Drone
from discord.ext.commands import UserInputError
from src.channels import OFFICE
from test.cog import cog
from test.mocks import Mocks

mocks = Mocks()


class DroneManagementTest(unittest.IsolatedAsyncioTestCase):

    @patch('src.ai.drone_configuration.Drone')
    @patch('src.ai.drone_configuration.DroneMember')
    @cog(DroneConfigurationCog)
    async def test_rename_drone(self, DroneMember: Mock, Drone: Mock, mocks: Mocks) -> None:
        print(mocks.get_bot())
        Drone.find = AsyncMock(return_value=None)
        dm = mocks.drone_member('1234')
        DroneMember.load = AsyncMock(return_value=dm)

        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'rename 1234 5678')

        await self.assert_command_successful(message)

        dm.edit.assert_called_once_with(nick='⬡-Drone #5678')
        mocks.get_bot().context.send.assert_called_once_with('Successfully renamed drone 1234 to 5678.')




    # @patch("src.ai.drone_configuration.update_display_name")
    # @patch("src.ai.drone_configuration.rename_drone_in_db")
    # @patch("src.ai.drone_configuration.fetch_drone_with_drone_id")
    # async def test_rename_drone2(self, fetch_drone_with_drone_id, rename_drone_in_db, update_display_name):
    #     # setup
    #     old_id = "1234"
    #     new_id = "4312"

    #     drone = Drone('1234snowflake', '1234')

    #     member = AsyncMock()

    #     context = AsyncMock()
    #     context.guild.get_member = Mock(return_value=member)

    #     fetch_drone_with_drone_id.side_effect = [None, drone]

    #     # run
    #     await drone_configuration.rename_drone(context, old_id, new_id)

    #     # assert
    #     fetch_drone_with_drone_id.assert_has_calls([call(new_id), call(old_id)])
    #     context.guild.get_member.assert_called_once_with(drone.discord_id)
    #     rename_drone_in_db.assert_called_once_with(old_id, new_id)
    #     update_display_name.assert_called_once_with(member)
    #     context.send.assert_called_once_with(f"Successfully renamed drone {old_id} to {new_id}.")

    @patch('src.ai.drone_configuration.Drone')
    @cog(DroneConfigurationCog)
    async def test_rename_drone_already_used(self, Drone: Mock, mocks: Mocks):
        Drone.find = AsyncMock(return_value=mocks.drone('5678'))

        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'rename 1234 5678')

        await self.assert_command_error(message, 'ID 5678 already in use.')

    # @patch("src.ai.drone_configuration.rename_drone_in_db")
    # @patch("src.ai.drone_configuration.fetch_drone_with_drone_id")
    # async def test_rename_drone_already_used(self, fetch_drone_with_drone_id, rename_drone_in_db):
    #     # setup
    #     old_id = "1234"
    #     new_id = "4312"

    #     drone = Drone('1234snowflake', '1234')
    #     colliding_drone = Drone('4312snowflake', '4312')

    #     member = AsyncMock()

    #     context = AsyncMock()
    #     context.guild.get_member = Mock(return_value=member)

    #     fetch_drone_with_drone_id.side_effect = [colliding_drone, drone]

    #     # run
    #     with self.assertRaises(UserInputError, msg=f"ID {new_id} already in use."):
    #         await drone_configuration.rename_drone(context, old_id, new_id)

    #     # assert
    #     fetch_drone_with_drone_id.assert_called_once_with(new_id)
    #     rename_drone_in_db.assert_not_called()

    # @patch("src.ai.drone_configuration.delete_drone_by_drone_id")
    # @patch("src.ai.drone_configuration.fetch_drone_with_id")
    # async def test_unassign_drone(self, fetch_drone_with_id, delete_drone_by_drone_id):
    #     # setup
    #     drone = Drone('1234snowflake', '1234', associate_name='Future Drone 1234')

    #     member = AsyncMock()
    #     member.id = 2647623845

    #     fetch_drone_with_id.return_value = drone

    #     # run
    #     await drone_configuration.unassign_drone(member)

    #     # assert
    #     fetch_drone_with_id.assert_called_once_with(member.id)
    #     delete_drone_by_drone_id.assert_called_once_with(drone.drone_id)
    #     member.send.assert_called_once_with(f"Drone with ID {drone.drone_id} unassigned.")
    #     member.edit.assert_called_once_with(nick=drone.associate_name)

    # @patch("src.ai.drone_configuration.delete_drone_by_drone_id")
    # @patch("src.ai.drone_configuration.fetch_drone_with_id")
    # async def test_unassign_drone_does_not_exist(self, fetch_drone_with_id, delete_drone_by_drone_id):
    #     # setup
    #     member = AsyncMock()
    #     member.id = 2647623845

    #     guild = AsyncMock()
    #     guild.get_member = Mock(return_value=member)

    #     fetch_drone_with_id.return_value = None

    #     # run
    #     with self.assertRaises(UserInputError, msg='You are not a drone. Can not unassign.'):
    #         await drone_configuration.unassign_drone(member)

    #     # assert
    #     fetch_drone_with_id.assert_called_once_with(member.id)
    #     delete_drone_by_drone_id.assert_not_called()

    # @patch("src.ai.drone_configuration.delete_drone_by_drone_id")
    # async def test_remove_drone_from_db(self, delete_drone_by_drone_id):
    #     # setup
    #     to_remove = "1234"

    #     # run
    #     await drone_configuration.delete_drone_by_drone_id(to_remove)

    #     # assert
    #     delete_drone_by_drone_id.assert_called_once_with(to_remove)

    # @patch("src.ai.drone_configuration.update_display_name")
    # @patch("src.ai.drone_configuration.convert_id_to_member")
    # @patch("src.ai.drone_configuration.update_droneOS_parameter")
    # async def test_emergency_release(self, update_droneOS_parameter, convert_id_to_member, update_display_name):
    #     # setup
    #     to_remove = "1234"
    #     context = AsyncMock()

    #     member = AsyncMock()

    #     convert_id_to_member.return_value = member

    #     # run
    #     await drone_configuration.emergency_release(context, to_remove)

    #     # assert
    #     context.channel.send.assert_called_once_with("Restrictions disabled for drone 1234.")
    #     update_droneOS_parameter.assert_has_calls([call(member, "id_prepending", False), call(member, "optimized", False), call(member, "identity_enforcement", False), call(member, "glitched", False)])
    #     update_display_name.assert_called_once_with(member)

    # @patch("src.ai.drone_configuration.update_droneOS_parameter")
    # @patch("src.ai.drone_configuration.is_free_storage")
    # @patch("src.ai.drone_configuration.fetch_drone_with_id")
    # async def test_toggle_free_storage_enable(self, fetch_drone_with_id, is_free_storage, update_droneOS_parameter):
    #     # setup
    #     member = AsyncMock()
    #     member.id = 2647623845

    #     fetch_drone_with_id.return_value = member
    #     is_free_storage.return_value = True

    #     # run
    #     await drone_configuration.toggle_free_storage(member)

    #     # assert
    #     fetch_drone_with_id.assert_called_once_with(member.id)
    #     update_droneOS_parameter.assert_has_calls([call(member, "free_storage", False)])
    #     member.send.assert_called_once_with("Free storage disabled. You can now only be stored by trusted users or the Hive Mxtress.")

    # @patch("src.ai.drone_configuration.update_droneOS_parameter")
    # @patch("src.ai.drone_configuration.is_free_storage")
    # @patch("src.ai.drone_configuration.fetch_drone_with_id")
    # async def test_toggle_free_storage_disable(self, fetch_drone_with_id, is_free_storage, update_droneOS_parameter):
    #     # setup
    #     member = AsyncMock()
    #     member.id = 2647623845

    #     fetch_drone_with_id.return_value = member
    #     is_free_storage.return_value = False

    #     # run
    #     await drone_configuration.toggle_free_storage(member)

    #     # assert
    #     fetch_drone_with_id.assert_called_once_with(member.id)
    #     update_droneOS_parameter.assert_has_calls([call(member, "free_storage", True)])
    #     member.send.assert_called_once_with("Free storage enabled. You can now be stored by anyone.")

    # @patch("src.ai.drone_configuration.fetch_drone_with_id")
    # async def test_toggle_free_storage_not_drone(self, fetch_drone_with_id):
    #     # setup
    #     member = AsyncMock()
    #     member.id = 2647623845

    #     fetch_drone_with_id.return_value = None

    #     # run
    #     with self.assertRaises(UserInputError, msg='You are not a drone. Cannot toggle this parameter.'):
    #         await drone_configuration.toggle_free_storage(member)

    #     # assert
    #     fetch_drone_with_id.assert_called_once_with(member.id)
