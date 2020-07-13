import discord

from channels import EVERYWHERE
from resources import DRONE_AVATAR
from roles import EVERYONE


class AI_Help():
    '''
    Can tell users which commands they can use in the current channel.
    '''

    def __init__(self, bot, modules):
        self.bot = bot
        self.on_message = [self.send_bot_help]
        self.on_ready = []
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = []
        self.roles_whitelist = [EVERYONE]
        self.roles_blacklist = []
        self.modules = modules
        self.help_content = {'name': 'help',
                             'value': 'you are using this right now'}

    async def send_bot_help(self, message: discord.Message):
        '''
        Compile and send an embed with information about available commands.
        '''
        if message.content.lower() != 'help':
            return False

        # prepare embed
        embed = discord.Embed(
            title='Help', description='These features can be used in this channel.', color=0xff66ff)
        embed.set_thumbnail(url=DRONE_AVATAR)

        # add help_content from all registered modules
        for module in self.modules:
            channel_valid = message.channel.name not in module.channels_blacklist and (
                message.channel.name in module.channels_whitelist or EVERYWHERE in module.channels_whitelist)
            if channel_valid:
                try:
                    if module.help_content is not None:
                        embed.add_field(**module.help_content, inline=False)
                except AttributeError:
                    pass

        await message.channel.send(embed=embed)
        return False
