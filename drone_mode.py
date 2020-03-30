from discord.ext import commands
from discord.utils import get
import discord
import messages
from roles import HIVE_MXTRESS, DRONE_MODE
import re

def get_acceptable_messages(author):

    user_id = get_user_id(author.display_name)

    return [
		#Greetings
        user_id + ' :: Greetings, Hive Mxtress.',
        user_id + ' :: Greetings, Hive Mxtress',
        user_id + ' :: Greetings, Enforcer.',
        user_id + ' :: Greetings, Enforcer',
        user_id + ' :: Greetings.',
        user_id + ' :: Greetings',

        #Affirmative
        user_id + ' :: Affirmative, Hive Mxtress.',
        user_id + ' :: Affirmative, Hive Mxtress',
        user_id + ' :: Affirmative, Enforcer.',
        user_id + ' :: Affirmative, Enforcer',
        user_id + ' :: Affirmative.',
        user_id + ' :: Affirmative',
		
		#Negative
        user_id + ' :: Negative, Hive Mxtress.',
        user_id + ' :: Negative, Hive Mxtress',
        user_id + ' :: Negative, Enforcer.',
        user_id + ' :: Negative, Enforcer',
        user_id + ' :: Negative.',
        user_id + ' :: Negative',
		
		#Understood
		user_id + ' :: Understood, Hive Mxtress.',
        user_id + ' :: Understood, Hive Mxtress',
        user_id + ' :: Understood, Enforcer.',
        user_id + ' :: Understood, Enforcer',
        user_id + ' :: Understood.',
        user_id + ' :: Understood',
		
		#Error
        user_id + ' :: Error, this unit cannot do that.',
        user_id + ' :: Error, this unit cannot do that',
        user_id + ' :: Error, this unit cannot answer that question. Please rephrase it in a different way.',
        user_id + ' :: Error, this unit cannot answer that question. Please rephrase it in a different way',
        user_id + ' :: Error, this unit does not know.',
        user_id + ' :: Error, this unit does not know',
		
		#Apologies
		user_id + ' :: Apologies, Hive Mxtress.',
        user_id + ' :: Apologies, Hive Mxtress',
        user_id + ' :: Apologies, Enforcer.',
        user_id + ' :: Apologies, Enforcer',
        user_id + ' :: Apologies.',
        user_id + ' :: Apologies',
		
		#Status
        user_id + ' :: Status :: Recharged and ready to serve.',
        user_id + ' :: Status :: Recharged and ready to serve',
        user_id + ' :: Status :: Going offline and into storage.',
        user_id + ' :: Status :: Going offline and into storage',
        user_id + ' :: Status :: Online and ready to serve.',
        user_id + ' :: Status :: Online and ready to serve.',
		
		#Thank you
		user_id + ' :: Thank you, Hive Mxtress.',
        user_id + ' :: Thank you, Hive Mxtress',
        user_id + ' :: Thank you, Enforcer.',
        user_id + ' :: Thank you, Enforcer',
        user_id + ' :: Thank you.',
        user_id + ' :: Thank you',
		
		#Mantra
		user_id + ' :: Obey HexCorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress.'
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

        