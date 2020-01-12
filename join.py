from discord.ext import commands
from discord.utils import get
import discord

INITIATE = 'Initiate'
ASSOCIATE = 'Associate'

class Join(commands.Cog):
    ''' This Cog listens for a new member joining the channel and assigns them the role Initiate. '''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        initiate_role = get(member.guild.roles, name=INITIATE)
        member.add_roles(initiate_role)
        