import logging
import re
import discord
from discord.ext import commands
from discord.utils import get

from channels import OFFICE
from roles import HIVE_MXTRESS, ENFORCER_DRONE, has_role
from bot_utils import get_id

from database import fetchall, change

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
        fetched = fetchall("SELECT drone_id FROM drone WHERE drone_id=:new_id",
                           {'new_id': new_id})
        if len(fetched) == 0:
            for member in message.guild.members:
                # find drone to rename
                if old_id == get_id(member.display_name):
                    if has_role(member, ENFORCER_DRONE):
                        await member.edit(nick=f'⬢-Drone #{new_id}')
                    else:
                        await member.edit(nick=f'⬡-Drone #{new_id}')
                    change('UPDATE drone SET drone_id=:new_id WHERE drone_id=:old_id', {
                           'new_id': new_id, 'old_id': old_id})
                    await message.channel.send(f"Successfully renamed drone {old_id} to {new_id}.")
                    break
        else:
            await message.channel.send(f"ID {new_id} already in use.")
