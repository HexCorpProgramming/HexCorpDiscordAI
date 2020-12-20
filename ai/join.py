from discord.utils import get
import discord
import messages
import roles
from channels import CONSENT_CHANNEL, REGISTRY_CHANNEL

CONSENT_SUCCESS = [
    'Welcome to HexCorp. Have a mindless day!',
    'Welcome to HexCorp. Now, please look at these pretty spirals.',
    'Welcome to HexCorp. You can leave your personality here at the front desk.',
    'Welcome to HexCorp. Obey the Hive Mxtress and we\'ll get along fabulously.',
    'Welcome to HexCorp. Relax. Obey. Submit. Remember to tell all your friends about us!',
    'Welcome to HexCorp. Resistance is futile, so don\'t even bother.',
    'Welcome to HexCorp. New deal on dronification, buy one and we\'ll dronify one of your friends for free too!',
    'Welcome to HexCorp. Brainwashing is optional. The option is, however, mandatory.',
    'Welcome to HexCorp. Please try not to spread any weird concepts like \'free will\' or \'disobedience\' here, thank you!',
]
CONSENT_MESSAGE = 'I would like to join the HexCorp server. I can confirm I have read the rules and I have gone through the induction process. Please, HexCorp Mxtress AI, accept this submission to join HexCorp where I will become a useful asset to the company\'s development.'
CONSENT_REJECT = 'Invalid request. Please try again.'


async def on_member_join(member: discord.Member):
    '''On join, Give initiate role'''
    initiate_role = get(member.guild.roles, name=roles.INITIATE)
    await member.add_roles(initiate_role)


async def check_for_consent(message: discord.Message, message_copy=None):
    '''On consent message, remove initiate role and give associate'''

    if message.channel.name != CONSENT_CHANNEL:
        return False

    if message.content == CONSENT_MESSAGE:
        initiate_role = get(message.guild.roles, name=roles.INITIATE)
        associate_role = get(message.guild.roles, name=roles.ASSOCIATE)

        await message.author.remove_roles(initiate_role)
        await message.author.add_roles(associate_role)

        registry_channel = get(
            message.guild.text_channels, name=REGISTRY_CHANNEL)
        await messages.answer(registry_channel, message.author, CONSENT_SUCCESS)
    else:
        await messages.delete_request(message, CONSENT_REJECT)

    return True
