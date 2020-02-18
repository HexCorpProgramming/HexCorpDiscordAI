from discord.ext import commands
from discord.utils import get
import discord
import messages
import roles
import re
from channels import GAGGING_CONTROL_CHANNEL


def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None


def mute_drone(member: discord.Member):
	pass

def unmute_drone(member: discord.Member):
	pass

def strip_recipient(message: str) -> str:
    '''
    Strip the recipient at the beginning of a received message.
    '''
    return re.sub(r'^<@!?\d*>', '', message, 1)

 @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.channel.name in []:
            return
				#check for and store whoever is atted

        if has_role(message.author, roles.HIVE_MXTRESS):
            #mute drone time
        	if has_role(message.author, roles.GAGGED):
            #already gagged
        	elif has_role(message.author, roles.DRONE):
            mute_drone