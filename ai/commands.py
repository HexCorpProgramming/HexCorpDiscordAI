from discord.ext.commands import Converter, BadArgument, Context
import discord

from id_converter import convert_id_to_member


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
