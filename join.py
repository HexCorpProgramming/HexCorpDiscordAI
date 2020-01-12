from discord.ext import commands
from discord.utils import get
import discord

INITIATE = 'Initiate'
ASSOCIATE = 'Associate'

CONSENT_CHANNEL = 'hexcorp-submission'
REGISTRY_CHANNEL = 'hexcorp-registry'

CONSENT_MESSAGE = 'I would like to join the HexCorp server. I can confirm I have read the rules and I have gone through the induction process. Please, HexCorp Mxtress AI, accept this submission to join HexCorp where I will become a useful asset to the company\'s development.'
CONSENT_ANSWER = 'Welcome to HexCorp. Have a mindless day!'
CONSENT_REJECT = 'Invalid request. Please try again.'


class Join(commands.Cog):
    ''' This Cog listens for a new member joining the channel and assigns them the role Initiate. '''

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        initiate_role = get(member.guild.roles, name=INITIATE)
        await member.add_roles(initiate_role)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.channel.name != CONSENT_CHANNEL:
            return

        if message.content == CONSENT_MESSAGE:
            initiate_role = get(message.guild.roles, name=INITIATE)
            associate_role = get(message.guild.roles, name=ASSOCIATE)

            await message.author.remove_roles(initiate_role)
            await message.author.add_roles(associate_role)
            
            registry_channel = get(message.guild.text_channels, name=REGISTRY_CHANNEL)
            await registry_channel.send(f'{message.author.mention}: {CONSENT_ANSWER}')
        else:
            await message.delete()
            await message.channel.send(f'{message.author.mention}: {CONSENT_REJECT}')
