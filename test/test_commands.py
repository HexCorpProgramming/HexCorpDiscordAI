from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch
from discord.ext.commands import BadArgument
from src.db.drone_dao import Drone

import src.ai.commands as commands


class NamedParameterConverterTest(IsolatedAsyncioTestCase):

    async def testConvertToInt(self):
        # init
        converter = commands.NamedParameterConverter("number", int)

        # run & assert
        self.assertEqual(await converter.convert(None, "-number=69"), 69)
        self.assertEqual(await converter.convert(None, "-number=0"), 0)
        self.assertEqual(await converter.convert(None, "-number=-1"), -1)
        with self.assertRaises(BadArgument):
            await converter.convert(None, "notAProperInput")
        with self.assertRaises(ValueError):
            await converter.convert(None, "-number=notANumber")


class DroneMemberConverterTest(IsolatedAsyncioTestCase):

    @patch('src.id_converter.get_discord_id_of_drone')
    async def test_convert(self, get_discord_id_of_drone):
        '''
        Ensure that a drone ID is converted to a memeber.
        '''

        context = Mock()
        member = Mock(id=222222)
        context.message.guild.get_member.return_value = member
        get_discord_id_of_drone.return_value = 222222

        converter = commands.DroneMemberConverter()
        self.assertEqual(member, await converter.convert(context, '1234'))

        get_discord_id_of_drone.assert_called_once_with('1234')

    @patch('src.id_converter.get_discord_id_of_drone')
    async def test_convert_invalid_id(self, get_discord_id_of_drone):
        '''
        Ensure that anything other than a drone ID is rejected.
        '''

        context = Mock()
        converter = commands.DroneMemberConverter()

        for arg in ['123, 12345', 'test']:
            with self.assertRaises(BadArgument):
                await converter.convert(context, arg)

        get_discord_id_of_drone.assert_not_called()

    @patch('src.id_converter.get_discord_id_of_drone')
    async def test_convert_non_drone(self, get_discord_id_of_drone):
        '''
        Ensure that an unassigned drone ID is rejected.
        '''

        context = Mock()
        converter = commands.DroneMemberConverter()
        get_discord_id_of_drone.return_value = None

        with self.assertRaises(BadArgument):
            await converter.convert(context, '1234')

        get_discord_id_of_drone.assert_called_once_with('1234')

    @patch('src.id_converter.get_discord_id_of_drone')
    async def test_convert_deleted_member(self, get_discord_id_of_drone):
        '''
        Ensure that an orphaned drone record is rejected.
        '''

        context = Mock()
        converter = commands.DroneMemberConverter()
        get_discord_id_of_drone.return_value = Drone(222222, '1234')
        context.message.guild.get_member.return_value = None

        with self.assertRaises(BadArgument):
            await converter.convert(context, '1234')

        get_discord_id_of_drone.assert_called_once_with('1234')
