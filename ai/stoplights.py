import discord
from discord.utils import get
from roles import MODERATION
from resources import CLOCK, TRAFFIC_LIGHTS


async def check_for_stoplights(message: discord.Message):
    if CLOCK in message.content:
        moderator_role = get(message.guild.roles, name=MODERATION)
        await message.channel.send(f"Moderators needed {moderator_role.mention}!")
        return True
    else:
        return any(traffic_light in message.content for traffic_light in TRAFFIC_LIGHTS)