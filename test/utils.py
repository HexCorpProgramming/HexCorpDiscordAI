from discord import Message, TextChannel
from discord.ext.commands import Bot, CheckFailure, Cog
from discord.utils import get
from functools import wraps
from typing import Any, Callable, Type
from src.bot_utils import COMMAND_PREFIX
from unittest.mock import AsyncMock, MagicMock


def cog(CogType: Type[Cog]) -> Callable[[Any, Any], Any]:
    '''
    A decorator factory for testing a Cog command.

    Adds a Bot parameter to the wrapped function.

    Use `bot.create_message()` to create the message for the command to execute.

    Usage:

    ```
    from test.utils import cog

    @cog(MyCog)
    async def test_my_cog(self, bot):
        message = bot.create_message('general', '!my_command with parameters')

        # Run MyCog.my_command('with', 'parameters') and ensure that its checks pass.
        await self.assert_command_successful(bot, message)
    ```
    '''

    def decorator(func: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
        '''
        A decorator to create and pass in a Bot object for testing with.
        '''

        # Create the bot
        bot = Bot(command_prefix=COMMAND_PREFIX)

        # Add the Cog under test to the bot.
        bot.add_cog(CogType(bot))

        # Give the bot a user as if it is connected to the server.
        bot._connection.user = AsyncMock(bot=True, id=2)

        # Set up some channels.
        channels = []

        for name in ['hex-office', 'hexcorp-transmissions']:
            channel = MagicMock(spec=TextChannel)
            channel.name = name
            channels.append(channel)

        # Create the author's Member record.
        author = AsyncMock(bot=False, id=1)

        # Create a message.
        def create_message(channel_name='', content='', **kwargs) -> Message:
            '''
            Create a new mock Message object.

            Channel: The channel name, e.g. general.
            Content: The message's text.
            '''

            guild = MagicMock()

            # These are called by the discord.Member parameter converter.
            guild.get_member_named.return_value = None
            guild.query_members = AsyncMock(return_value=[])

            message = AsyncMock(mentions=[], author=author)
            channel = get(channels, name=channel_name)

            if channel is not None:
                message.channel = channel
            else:
                channel = MagicMock(spec=TextChannel)
                channel.name = channel_name
                message.channel = channel
                guild.text_channels.append(channel)

            guild.text_channels = channels
            message.guild = guild
            message.content = content

            for n, v in kwargs.items():
                setattr(message, n, v)

            return message

        bot.create_message = create_message

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            '''
            Call the wrapped function, passing in the Bot as the last positional argument.
            '''

            # Patch assertions onto the Test class.  Note that they are async and must be awaited.
            # This is done so that they can use other assert* functions.
            self = args[0]
            self.assert_command_error = lambda bot, message: assert_command_error(self, bot, message)
            self.assert_command_successful = lambda bot, message: assert_command_successful(self, bot, message)

            return await func(*args, bot, **kwargs)

        return wrapper

    return decorator


async def run_command(bot: Bot, message: Message) -> Exception | None:
    '''
    Run a command and return the error that it produced.
    '''
    command_error = None

    async def on_error(cog, context, error) -> None:
        '''
        Store errors from the command.
        '''

        nonlocal command_error
        command_error = error

    for name, command in bot.prefixed_commands.items():
        command.on_error = on_error

    # Run the Cog command.
    await bot.process_commands(message)

    return command_error


async def assert_command_error(self, bot: Bot, message: Message) -> None:
    '''
    Ensure that a command invocation causes a check failure.
    '''

    command_error = await run_command(bot, message)

    # Check that an error was recorded.
    self.assertIsNotNone(command_error)

    # An exception was recorded but not the correct one.
    self.assertIsInstance(command_error, CheckFailure)


async def assert_command_successful(self, bot: Bot, message: Message) -> None:
    '''
    Ensure that a command invocation does not cause a check failure.
    '''

    command_error = await run_command(bot, message)

    self.assertIsNone(command_error)
