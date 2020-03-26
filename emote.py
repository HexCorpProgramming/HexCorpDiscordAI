from discord.ext import commands
from discord.utils import get
import discord
from channels import TRANSMISSIONS_CHANNEL, LEWD_TRANSMISSIONS_CHANNEL

acceptable_channels = [ TRANSMISSIONS_CHANNEL, LEWD_TRANSMISSIONS_CHANNEL ]

class Emote(commands.Cog):

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Emote cog online.")

    @commands.command()
    async def emote(self, ctx):
        if ctx.message.channel.name in acceptable_channels:
            message_to_convert = 
