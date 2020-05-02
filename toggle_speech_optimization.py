from discord.ext import commands
from discord.utils import get
import discord
from roles import HIVE_MXTRESS, SPEECH_OPTIMIZATION, has_role
from channels import EVERYWHERE


class Toggle_Speech_Optimization():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [EVERYWHERE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.dronemode]
        self.on_ready = []

    async def dronemode(self, message: discord.Message):

        print("Drone mode command triggered")

        if not message.content.lower().startswith('optimize '):
            print("Message doesn't start with what we want.")
            return False

        target_drone = message.mentions[0]
        if has_role(target_drone, SPEECH_OPTIMIZATION):
            await message.channel.send(f"Speech optimization deactivated for {target_drone.display_name}")
            await target_drone.remove_roles(get(message.guild.roles, name=SPEECH_OPTIMIZATION))
        else:
            await message.channel.send(f"Speech optimization activated for {target_drone.display_name}")
            await target_drone.add_roles(get(message.guild.roles, name=SPEECH_OPTIMIZATION))

        return True
