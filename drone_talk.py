from discord.ext import commands
from discord.utils import get
import discord
import messages
from roles import HIVE_MXTRESS, DRONE
from channels import COMMUNICATION_CHANNEL
import re

def get_user_id(username):
	drone_id = re.search(r"\d{4}", username).group()
	return drone_id if drone_id is not None else 0000;

def has_role(member: discord.Member, role: str) -> bool:
	return get(member.roles, name=role) is not None

class Drone_Talk(commands.Cog):

	def __init__(self,bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print("Drone talk cog online.")

	@commands.Cog.listener()
	async def on_message(self, message):

		if(message.channel.name == COMMUNICATION_CHANNEL):
			if(has_role(message.author, DRONE)):

				user_id = get_user_id(message.author.display_name)

				if(message.content.startswith(user_id + ' ::') == False):
					await message.delete()
