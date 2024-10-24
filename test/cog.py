from discord import Message
from discord.ext.commands import Bot, Cog, CommandError, Context, Converter, Greedy, MemberNotFound
from discord.utils import find
from functools import wraps
from inspect import iscoroutinefunction
from re import match, sub
from src.drone_member import DroneMember
from test.mocks import Mocks
from typing import Any, Callable, Type
from unittest.mock import AsyncMock, Mock, patch


class MockDroneMemberConverter(Converter):
    '''
    A parameter converter to automatically create DroneMember objects from command parameters.
    '''

    async def convert(self, context: Context, argument: str):
        '''
        Try to find a DroneMember that matches the "argument" string.
        '''

        member = None

        if context.guild:
            guild = context.guild
        else:
            guild = context.bot.guilds[0]

        members = guild._members.values()

        # Match by Discord ID.
        # An ID is an int with 15 to 20 digits.
        # Matches <@ID>, <#ID>.
        discord_id = match(r"<(?:@[!&]?|#)([0-9]{15,20})>$", argument)

        if discord_id is not None:
            discord_id = int(sub('[^0-9]', '', discord_id.group(1)))
            member = guild._members.get(discord_id)

        # Match by member name or nickname.
        if member is None:
            member = find(lambda m: m.name == argument or m.nick == argument, members)

        # Match by drone ID.
        if member is None:
            for m in members:
                drone = getattr(m, 'drone', None)

                if drone is not None and str(drone.drone_id) == argument:
                    member = m
                    break

        if member is None:
            raise MemberNotFound(argument)

        return member


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

        # This is designed to work only with async functions.
        if not iscoroutinefunction(func):
            raise RuntimeError('@cog can only be used on async functions')

        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            '''
            Call the wrapped function, passing in the Bot as the last positional argument.
            '''

            # The Mocks object contains a Guild and a Bot.
            mocks = Mocks()

            # Add the Cog under test to the bot.
            bot = mocks.get_bot()
            bot.add_cog(CogType(bot))

            # Patch assertions onto the Test class.  Note that they are async and must be awaited.
            # This is done so that they can use other assert* functions.
            self = args[0]
            self.assert_command_error = lambda message, error_message='': assert_command_error(self, bot, message, error_message)
            self.assert_command_successful = lambda message: assert_command_successful(self, bot, message)

            return await func(*args, mocks, **kwargs)

        return wrapper

    return decorator


@patch('src.drone_member.MemberConverter')
async def run_command(bot: Bot, message: Message, MemberConverter) -> Exception | None:
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

    # Create a command parameter converter.
    converter = MockDroneMemberConverter()

    # Modify each every bot command.
    for name, command in bot.prefixed_commands.items():
        # Override the error handler to store the result locally.
        command.on_error = on_error

        # Override any DroneMember parameter converters with one
        # that returns a mock DroneMember from the mock guild.
        for name, param in command.params.items():
            if isinstance(param._annotation, Greedy):
                if param._annotation.converter == DroneMember:
                    param._annotation.converter = converter
            else:
                if param._annotation == DroneMember:
                    param._annotation = converter

    context = await bot.get_context(message)

    # Mock asynchronous Messageable methods.
    for name in 'reply', 'send', 'trigger_typing', 'fetch_message':
        setattr(context, name, AsyncMock())

    # Mock synchronous Messageable methods.
    for name in 'typing', 'can_send', 'history':
        setattr(context, name, Mock())

    # Store the context on the bot so it can be accessed later, for example:
    # mocks.get_bot().context.assert_called_once()
    bot.context = context

    await bot.invoke(context)

    return command_error


async def assert_command_error(self, bot: Bot, message: Message, error_message: str = '') -> None:
    '''
    Ensure that a command invocation causes a check failure.
    '''

    command_error = await run_command(bot, message)

    # Check that an error was recorded.
    self.assertIsNotNone(command_error)

    # An exception was recorded but not the correct one.
    self.assertIsInstance(command_error, CommandError)

    if error_message != '':
        self.assertEqual(error_message, str(command_error))


async def assert_command_successful(self, bot: Bot, message: Message) -> None:
    '''
    Ensure that a command invocation does not cause a check failure.
    '''

    command_error = await run_command(bot, message)

    self.assertIsNone(command_error)
