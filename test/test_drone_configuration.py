import unittest
from unittest.mock import AsyncMock, patch, MagicMock, Mock

import src.roles as roles
from src.ai.drone_configuration import DroneConfigurationCog
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

    @patch('src.ai.drone_configuration.Drone')
    @cog(DroneConfigurationCog)
    async def test_rename_drone_already_used(self, Drone: Mock, mocks: Mocks) -> None:
        Drone.find = AsyncMock(return_value=mocks.drone('5678'))

        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'rename 1234 5678')

        await self.assert_command_error(message, 'ID 5678 already in use.')

    @patch('src.ai.drone_configuration.DroneMember')
    @cog(DroneConfigurationCog)
    async def test_unassign_drone(self, DroneMember: MagicMock, mocks: Mocks) -> None:
        drone_member = mocks.drone_member('1234')
        DroneMember.load = AsyncMock(return_value=drone_member)

        message = mocks.direct_command(drone_member, 'unassign')

        await self.assert_command_successful(message)

        drone_member.edit.assert_called_once_with(nick=drone_member.drone.associate_name)
        drone_member.add_roles.assert_called_once_with(mocks.role(roles.ASSOCIATE))
        drone_member.drone.delete.assert_called_once()
        drone_member.send.assert_called_once_with('Drone with ID 1234 unassigned.')

    @patch('src.ai.drone_configuration.DroneMember')
    @cog(DroneConfigurationCog)
    async def test_unassign_drone_does_not_exist(self, DroneMember: MagicMock, mocks: Mocks) -> None:
        author = mocks.drone_member('1234', drone=None)
        DroneMember.load = AsyncMock(return_value=author)

        message = mocks.direct_command(author, 'unassign')

        await self.assert_command_error(message, 'You are not a drone. Can not unassign.')

    @cog(DroneConfigurationCog)
    async def test_emergency_release(self, mocks: Mocks) -> None:
        author = mocks.drone_member('1234', roles=[roles.MODERATION])
        target = mocks.drone_member('5678')

        message = mocks.command(author, '', 'emergency_release 5678')

        await self.assert_command_successful(message)

        target.drone.save.assert_called_once()
        mocks.channel('').send.assert_called_once_with("Restrictions disabled for drone 5678.")
        self.assertFalse(target.drone.id_prepending)
        self.assertFalse(target.drone.optimized)
        self.assertFalse(target.drone.identity_enforcement)
        self.assertFalse(target.drone.third_person_enforcement)
        self.assertFalse(target.drone.glitched)
        self.assertFalse(target.drone.is_battery_powered)
        self.assertTrue(target.drone.can_self_configure)

    @cog(DroneConfigurationCog)
    async def test_toggle_free_storage_enable(self, mocks: Mocks) -> None:
        # setup
        author = mocks.drone_member('1234')
        message = mocks.direct_command(author, 'toggle_free_storage')

        # run
        await self.assert_command_successful(message)

        # assert
        self.assertTrue(author.drone.free_storage)
        author.drone.save.assert_called_once()

    @cog(DroneConfigurationCog)
    async def test_toggle_free_storage_disable(self, mocks: Mocks) -> None:
        # setup
        author = mocks.drone_member('1234', drone_free_storage=True)
        message = mocks.direct_command(author, 'toggle_free_storage')

        # run
        await self.assert_command_successful(message)

        # assert
        self.assertFalse(author.drone.free_storage)
        author.drone.save.assert_called_once()

    @cog(DroneConfigurationCog)
    async def test_toggle_free_storage_not_drone(self, mocks: Mocks) -> None:
        # setup
        author = mocks.drone_member('1234', drone=None)
        message = mocks.direct_command(author, 'toggle_free_storage')

        # run
        await self.assert_command_error(message, 'You are not a drone. Cannot toggle this parameter.')
