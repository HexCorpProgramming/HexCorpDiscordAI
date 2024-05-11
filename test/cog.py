from discord import Message
from discord.ext.commands import Bot, CheckFailure, Cog
from functools import wraps
from typing import Any, Callable, Type
from unittest.mock import AsyncMock, patch
from test.mocks import Mocks


def cog(CogType: Type[Cog]) -> Callable[[Any, Any], Any]:
    '''
    A decorator factory for testing a Cog command.

    Adds a Mocks parameter to the wrapped function.

    Use `mocks.message()` to create the message for the command to execute.

    Usage:

    ```
    from test.utils import cog

    @cog(MyCog)
    async def test_my_cog(self, mocks):
        message = bot.create_message('general', '!my_command with parameters')

        # Run MyCog.my_command('with', 'parameters') and ensure that its checks pass.
        await self.assert_command_successful(message)
    ```
    '''

    def decorator(func: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
        '''
        A decorator to create and pass in a Mocks object for testing with.
        '''

        # The Mocks object contains a Guild and a Bot.
        mocks = Mocks()

        # Add the Cog under test to the bot.
        mocks.get_bot().add_cog(CogType(mocks.get_bot()))

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            '''
            Call the wrapped function, passing in the Bot as the last positional argument.
            '''

            # Patch assertions onto the Test class.  Note that they are async and must be awaited.
            # This is done so that they can use other assert* functions.
            self = args[0]
            self.assert_command_error = lambda message: assert_command_error(self, message.guild._bot, message)
            self.assert_command_successful = lambda message: assert_command_successful(self, message.guild._bot, message)

            return await func(*args, mocks, **kwargs)

        return wrapper

    return decorator


@patch('src.drone_member.MemberConverter')
@patch('src.drone_member.Drone', new_callable=AsyncMock)
async def run_command(bot: Bot, message: Message, Drone, MemberConverter) -> Exception | None:
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

    MemberConverter.return_value = AsyncMock()
    MemberConverter.return_value.convert.side_effect = message.guild.drone_members['members']
    Drone.find.side_effect = message.guild.drone_members['drones']

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
