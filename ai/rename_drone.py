import logging
import re
import discord
from discord.ext import commands
from discord.utils import get

from channels import OFFICE
from roles import HIVE_MXTRESS, ENFORCER_DRONE, has_role
from bot_utils import get_id

from db.drone_dao import rename_drone, fetch_drone_with_drone_id

LOGGER = logging.getLogger('ai')


class RenameDrone():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [OFFICE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.rename]
        self.on_ready = []
        self.help_content = {
            'name': 'rename', 'value': 'changes a drones ID to a currently unused one'}

    async def rename(self, message: discord.Message):
        if not message.content.lower().startswith('rename '):
            return False

        LOGGER.debug('Message is valid for renaming a drone.')

        # get entered IDs
        ids = re.findall(r"\d{4}", message.content)
        if len(ids) < 2:
            await message.channel.send("Invalid usage of command.")
            return False
        old_id = ids[0]
        new_id = ids[1]

        # check for collisions
        collision = fetch_drone_with_drone_id(new_id)
        if collision is None:
            drone = fetch_drone_with_drone_id(old_id)
            member = self.bot.guilds[0].get_member(drone.id)
            rename_drone(old_id, new_id)
            if has_role(member, ENFORCER_DRONE):
                await member.edit(nick=f'⬢-Drone #{new_id}')
            else:
                await member.edit(nick=f'⬡-Drone #{new_id}')
            await message.channel.send(f"Successfully renamed drone {old_id} to {new_id}.")
        else:
            await message.channel.send(f"ID {new_id} already in use.")
