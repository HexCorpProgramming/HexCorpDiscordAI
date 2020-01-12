from discord.ext import commands
import discord
import random

INITIATE_ROLE = 'Initiate'

class Join(commands.Cog):
    ''' This Cog listens for a new member joining the channel and assigns them the role Initiate'''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for role in self.bot.guilds[0].roles:
            if role.name == INITIATE_ROLE:
                self.initiate_role = role
                return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        member.add_roles(self.initiate_role)
        