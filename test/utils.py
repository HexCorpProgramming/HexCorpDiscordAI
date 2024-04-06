from asyncio import get_running_loop, timeout
from discord import Message, TextChannel
from discord.ext.commands import Bot, Cog, Context
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
    @cog(MyCog)
    async def test_my_cog(self, bot):
        message = bot.create_message('general', '!my_command with parameters')

        # Run MyCog.my_command('with', 'parameters') and ensure that its checks pass.
        await assert_command_successful(bot, message)
    ```
    '''

    def decorator(func: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
        '''
        A decorator to create and pass in a Bot object for testing with.
        '''

        async def r(context: Context, exception: Exception) -> None:
            '''
            The error handler for the bot.
            When a CheckFailure exception is raised this function will be called and it will
            save the exception to the `message.err` future.
            '''

            context.message.err.set_result(exception)

        # Create the bot
        bot = Bot(command_prefix=COMMAND_PREFIX)

        # Register the error handler.
        bot.on_command_error = r

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

            message = AsyncMock(mentions=[], author=author)
            channel = get(channels, name=channel_name)

            if channel is not None:
                message.channel = channel
            else:
                channel = MagicMock(spec=TextChannel)
                channel.name = channel_name
                message.channel = channel
                message.guild.text_channels.append(channel)

            message.guild.text_channels = channels
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

            return await func(*args, bot, **kwargs)

        return wrapper

    return decorator


async def assert_command_error(bot: Bot, message: Message) -> None:
    '''
    Ensure that a command invocation causes a check failure.
    '''

    message.err = get_running_loop().create_future()

    # Run the Cog command.
    await bot.process_commands(message)

    # Wait for the on_error handler to be called.
    async with timeout(0.1):
        await message.err

    # Check that an error was recorded.
    if not isinstance(message.err.result(), Exception):
        raise Exception('Expected CheckFailure was not raised')


async def assert_command_successful(bot: Bot, message: Message) -> None:
    '''
    Ensure that a command invocation does not cause a check failure.
    '''

    message.err = get_running_loop().create_future()

    # Run the Cog command.
    await bot.process_commands(message)

    # Wait for the on_error handler to be called.
    try:
        async with timeout(0.1):
            await message.err
            raise message.err.result()
    except TimeoutError:
        # Success: The command did not raise an error.
        pass
