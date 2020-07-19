import discord
from discord.utils import get
from discord.ext import commands
from roles import has_role

async def toggle_role(targets: List[discord.Member], context, role_name: str):

    if (role := get(context.guild.roles, name = role_name)) is None: return

    for target in targets:
        if has_role(target, role_name):
            print("Removing role.")
        else:
            print("Adding role.")

    print("Hello world")





