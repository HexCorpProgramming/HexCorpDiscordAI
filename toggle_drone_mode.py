from discord.ext import commands
from discord.utils import get
import discord
from roles import HIVE_MXTRESS, DRONE_MODE, has_role
from channels import EVERYWHERE


class Toggle_Drone_Mode():

    def __init__(self, bot):
        self.bot = bot
        self.channels = [EVERYWHERE]
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.dronemode]
        self.on_ready = []

    async def dronemode(self, message: discord.Message):
        if not message.content.lower().startswith('dronemode '):
            return False

        target_drone = message.mentions[0]
        if has_role(target_drone, DRONE_MODE):
            await message.channel.send("DroneMode role toggled off for " + target_drone.display_name)
            await target_drone.remove_roles(get(message.guild.roles, name=DRONE_MODE))
        else:
            await message.channel.send("DroneMode role toggled on for " + target_drone.display_name)
            await target_drone.add_roles(get(message.guild.roles, name=DRONE_MODE))

        return True
