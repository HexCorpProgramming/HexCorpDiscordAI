from discord.ext import commands
from discord.utils import get
import discord
import messages
import roles
import re
from channels import GAGGING_CONTROL_CHANNEL

drone_role = get(member.guild.roles, name=roles.DRONE)
associate_role = get(member.guild.roles, name=roles.ASSOCIATE)
gagged_role = get(member.guild.roles, name=roles.GAGGED)



def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None


def mute_drone(member: discord.Member):
  await member.add_roles(gagged_role)

	if has_role(member, associate_role):
		await member.remove_roles(associate_role)
	if has_role(member, drone_role):
		await member.remove_roles(drone_role)

def unmute_drone(member: discord.Member):
	await member.remove_roles(gagged_role)
	#if name starts with filled hex give drone etc.


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