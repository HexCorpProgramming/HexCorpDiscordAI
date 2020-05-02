import discord
from channels import EVERYWHERE
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
        self.embed_thumbnail = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"

    async def send_bot_help(self, message: discord.Message):
        '''
        Compile and send an embed with information about available commands.
        '''
        if message.content.lower() != 'help':
            return False

        # prepare embed
        embed = discord.Embed(title='Help', description='These features can be used in this channel.', color=0xff66ff)
        embed.add_field(**self.help_content, inline=False)
        embed.set_thumbnail(url=self.embed_thumbnail)

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
