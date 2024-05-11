from discord.ext.commands import CheckFailure


class ValidationError(CheckFailure):
    '''
    An error that should be reported to the user.
    '''
