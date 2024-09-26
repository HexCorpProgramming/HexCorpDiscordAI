from discord.ext.commands import BadArgument, Context, Converter


class NamedParameterConverter(Converter):

    def __init__(self, argument_name: str, type_converter):
        self.argument_name = argument_name
        self.type_converter = type_converter

    async def convert(self, context: Context, argument: str):
        '''
        Parses the given value to see if it fits the flag parameter pattern and if so returns the given value in the specified type.
        '''
        if not argument.startswith(f"-{self.argument_name}="):
            raise BadArgument(f'Expected -{self.argument_name}=')

        argument_value = argument.split('=')[1]

        return self.type_converter(argument_value)
