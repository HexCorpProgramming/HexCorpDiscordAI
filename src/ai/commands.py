import discord
from discord.ext.commands import BadArgument, Context, Converter

from src.id_converter import convert_id_to_member


class DroneMemberConverter(Converter):
    async def convert(self, context: Context, argument: str) -> discord.Member:
        '''
        Converts a given argument to a Member that is a drone. Raises BadArgument otherwise.
        Does not handle mentions. Those should be handled by the default converter.
        '''
        member = convert_id_to_member(context.message.guild, argument)

        if member is not None:
            return member
        else:
            raise BadArgument


class NamedParameterConverter(Converter):

    def __init__(self, argument_name: str, type_converter):
        self.argument_name = argument_name
        self.type_converter = type_converter

    async def convert(self, context: Context, argument: str):
        '''
        Parses the given value to see if it fits the flag parameter pattern and if so returns the given value in the specified type.
        '''
        if not argument.startswith(f"-{self.argument_name}="):
            raise BadArgument

        argument_value = argument.split('=')[1]

        return self.type_converter(argument_value)
