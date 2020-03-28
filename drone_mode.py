from discord.ext import commands
from discord.utils import get
import discord
import messages
from roles import HIVE_MXTRESS, DRONE_MODE
import re

def get_acceptable_messages(author):

    user_id = get_user_id(author.display_name)

    return [
        user_id + ' :: Yes, Hive Mxtress.',
        user_id + ' :: No, Hive Mxtress.',
        user_id + ' :: Yes, Hive Mxtress',
        user_id + ' :: No, Hive Mxtress'
    ]

def get_user_id(username):
    drone_id = re.search(r"\d{4}", username).group()
    return drone_id if drone_id is not None else 0000;

def has_role(member: discord.Member, role: str) -> bool:
    return get(member.roles, name=role) is not None

class Drone_Mode(commands.Cog):

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Drone mode cog online.")

    @commands.Cog.listener()
    async def on_message(self, message):
        #If the message is written by a drone mode drone, and the message is NOT a valid message, delete it.
        if(has_role(message.author, DRONE_MODE)):
            if(message.content not in get_acceptable_messages(message.author)):
                await message.delete()

    @commands.command()
    async def dronemode(self, context):
        if(has_role(context.message.author, HIVE_MXTRESS)):
            target_drone = context.message.mentions[0]
            if has_role(target_drone, DRONE_MODE):
                await context.send("DroneMode role toggled off for " + target_drone.display_name)
                await target_drone.remove_roles(get(context.guild.roles, name=DRONE_MODE))
            else:
                await context.send("DroneMode role toggled on for " + target_drone.display_name)
                await target_drone.add_roles(get(context.guild.roles, name=DRONE_MODE))
        else:
            await context.send("This command can only be used by the Hive Mxtress.")

        