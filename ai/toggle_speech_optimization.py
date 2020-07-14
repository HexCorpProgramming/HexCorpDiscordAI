import logging

import discord
from discord.ext import commands
from discord.utils import get

from channels import EVERYWHERE

from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, has_role


LOGGER = logging.getLogger('ai')

async def toggle(context, target_drones):
    for drone in target_drones:
        if has_role(drone, SPEECH_OPTIMIZATION):
            await context.send(f"Speech optimization deactivated for {drone.display_name}")
            await drone.remove_roles(get(context.guild.roles, name=SPEECH_OPTIMIZATION))
        else:
            await context.send(f"Speech optimization activated for {drone.display_name}")
            await drone.add_roles(get(context.guild.roles, name=SPEECH_OPTIMIZATION))