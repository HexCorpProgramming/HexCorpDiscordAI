import unittest
from src.ai.drone_os_status import DroneOsStatusCog
import src.roles as roles
from test.cog import cog
from test.mocks import Mocks


class DroneOSStatusTest(unittest.IsolatedAsyncioTestCase):

    @cog(DroneOsStatusCog)
    async def asyncSetUp(self, mocks: Mocks) -> None:
        self.mocks = mocks

    async def test_status_no_drone(self) -> None:
        # setup
        member = self.mocks.drone_member('1234', drone=None)
        message = self.mocks.command(member, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_error(message, 'The specified member is not a drone')

    async def test_status_not_trusted(self) -> None:
        # setup
        member = self.mocks.drone_member('1234', drone_trusted_users=[123])
        author = self.mocks.member('author', id=1)
        message = self.mocks.command(author, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_error(message, 'You are not registered as a trusted user of this drone.')

    async def test_status(self) -> None:
        # setup
        member = self.mocks.drone_member('1234', drone_trusted_users=[123], drone_optimized=True, drone_battery_minutes=300)
        author = self.mocks.member('author', id=123)
        message = self.mocks.command(author, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_successful(message)

        author.send.assert_called_once()
        embed = author.send.call_args.kwargs['embed']
        self.assertEqual("You are registered as a trusted user of this drone and have access to its data.", embed.description)
        self.assertEqual("Optimized", embed.fields[0].name)
        self.assertEqual("Enabled", embed.fields[0].value)
        self.assertEqual("Glitched", embed.fields[1].name)
        self.assertEqual("Disabled", embed.fields[1].value)
        self.assertEqual("ID prepending required", embed.fields[2].name)
        self.assertEqual("Disabled", embed.fields[2].value)

    async def test_status_on_self(self) -> None:
        # setup
        self.mocks.member('A trustworthy user', id=123)
        member = self.mocks.drone_member('1234', drone_trusted_users=[123], drone_optimized=True, drone_battery_minutes=300)
        message = self.mocks.command(member, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_successful(message)

        member.send.assert_called_once()
        embed = member.send.call_args.kwargs['embed']
        self.assertEqual("Welcome, ⬡-Drone #1234", embed.description)
        self.assertEqual("Optimized", embed.fields[0].name)
        self.assertEqual("Enabled", embed.fields[0].value)
        self.assertEqual("Glitched", embed.fields[1].name)
        self.assertEqual("Disabled", embed.fields[1].value)
        self.assertEqual("ID prepending required", embed.fields[2].name)
        self.assertEqual("Disabled", embed.fields[2].value)
        self.assertEqual("Trusted users", embed.fields[8].name)
        self.assertEqual(str(["A trustworthy user"]), embed.fields[8].value)

    async def test_status_on_self_dangling_trusted_user(self) -> None:
        member = self.mocks.drone_member('1234', drone_trusted_users=[120], drone_optimized=True, drone_battery_minutes=300)
        message = self.mocks.command(member, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_successful(message)

        member.send.assert_called_once()
        embed = member.send.call_args.kwargs['embed']
        self.assertEqual("Welcome, ⬡-Drone #1234", embed.description)
        self.assertEqual("Optimized", embed.fields[0].name)
        self.assertEqual("Enabled", embed.fields[0].value)
        self.assertEqual("Glitched", embed.fields[1].name)
        self.assertEqual("Disabled", embed.fields[1].value)
        self.assertEqual("ID prepending required", embed.fields[2].name)
        self.assertEqual("Disabled", embed.fields[2].value)
        self.assertEqual("Trusted users", embed.fields[8].name)
        self.assertEqual(str([]), embed.fields[8].value)

    async def test_status_as_moderator(self) -> None:
        author = self.mocks.member('A Moderator', roles=[roles.MODERATION])
        member = self.mocks.drone_member('1234', drone_optimized=True, drone_battery_minutes=300)
        message = self.mocks.command(author, 'general', 'drone_status ' + member.mention)

        # run
        await self.assert_command_successful(message)

        author.send.assert_called_once()
        embed = author.send.call_args.kwargs['embed']
        self.assertEqual("You are a moderator and have access to this drone's data.", embed.description)
        self.assertEqual("Optimized", embed.fields[0].name)
        self.assertEqual("Enabled", embed.fields[0].value)
        self.assertEqual("Glitched", embed.fields[1].name)
        self.assertEqual("Disabled", embed.fields[1].value)
        self.assertEqual("ID prepending required", embed.fields[2].name)
        self.assertEqual("Disabled", embed.fields[2].value)
