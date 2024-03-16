import unittest
from unittest.mock import AsyncMock, Mock, patch
from src.ai.status import read_version, get_list_of_commands, get_list_of_listeners, report_status


class TestStatus(unittest.IsolatedAsyncioTestCase):
    '''
    Test the "ai_status" command.
    '''

    @patch("src.ai.status.Path")
    def test_read_version(self, Path):
        '''
        read_version should read the Git HEAD file.
        '''

        # An error message is returned if the file does not exist.
        Path.return_value.exists.return_value = False
        Path.return_value.read_text.side_effect = FileNotFoundError()
        self.assertEqual('[unable to read version information]', read_version())

        # An error message is returned if the file cannot be read.
        Path.return_value.exists.return_value = True
        Path.return_value.read_text.side_effect = PermissionError()
        self.assertEqual('[unable to read version information]', read_version())

        # The correct file is read and its value is returned.
        Path.return_value.exists.return_value = True
        Path.return_value.read_text.side_effect = None
        Path.return_value.read_text.return_value = 'refs/heads/v1.2.3'
        self.assertEqual('refs/heads/v1.2.3', read_version())

    def test_get_list_of_commands(self):
        '''
        get_list_of_commands should return a list of all available bot commands.
        '''

        context = Mock()
        context.bot = Mock()

        cmd1 = Mock()
        cmd1.name = "Command 1"

        cmd2 = Mock()
        cmd2.name = "Command 2"

        context.bot.commands = [cmd1, cmd2]
        commands = get_list_of_commands(context)

        self.assertEqual(["Command 1", "Command 2"], commands)

    def test_get_list_of_listeners(self):
        '''
        Ensure that get_list_of_listners returns the names of listener functions.
        '''

        listener1 = Mock()
        listener2 = Mock()
        listener1.__name__ = 'listener1'
        listener2.__name__ = 'listener2'

        listeners = get_list_of_listeners([listener1, listener2])

        self.assertEqual(['listener1', 'listener2'], listeners)

    @patch("src.ai.status.Path")
    async def test_report_status(self, Path):
        Path.return_value.read_text.return_value = 'refs/heads/v1.2.3'
        context = AsyncMock()
        listeners = [Mock()]
        listeners[0].__name__ = 'listener'

        context.bot.commands = [Mock()]
        context.bot.commands[0].name = 'command'

        await report_status(context, listeners)

        # The status should send an embed.
        context.send.assert_called_once()

        # The embed should contain three fields.
        embed = context.send.call_args.kwargs['embed']
        self.assertEqual(3, len(embed.fields))

        # Ensure that the version was set correctly.
        self.assertEqual('refs/heads/v1.2.3', embed.fields[0].value)

        # Ensure that the command list was set correctly.
        self.assertEqual("['command']", embed.fields[1].value)

        # Ensure that the listener list was set correctly.
        self.assertEqual("['listener']", embed.fields[2].value)
