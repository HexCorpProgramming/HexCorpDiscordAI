import discord
from discord.utils import get

ADMIN = 'admin'
HIVE_MXTRESS = 'Hive Mxtress'

async def delete_request(message: discord.Message, reject_message = None):
    admin_role = get(message.guild.roles, name=ADMIN)
    hive_mxtress_role = get(message.guild.roles, name=HIVE_MXTRESS)

    if admin_role in message.author.roles or hive_mxtress_role in message.author.roles:
        return
    
    await message.delete()

    if reject_message is not None:
        await message.channel.send(f'{message.author.mention}: {reject_message}')