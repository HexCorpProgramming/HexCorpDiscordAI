import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

from channels import OFFICE
from roles import DRONE, ENFORCER_DRONE, GLITCHED, STORED, HIVE_MXTRESS, ASSOCIATE, has_role

from database import change, fetchall
from bot_utils import get_id

LOGGER = logging.getLogger('ai')


class UnassignDrone():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [OFFICE]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.unassign]
        self.on_ready = []
        self.help_content = {'name': 'unassign',
                             'value': 'removes your drone status'}

    async def unassign(self, message: discord.Message):
        # TODO: get a more complex messsage to avoid accidental unassignment
        if not message.content.lower().startswith('unassign '):
            return False

        drone_id = get_id(message.content)
        # check for existence
        fetched = fetchall("SELECT drone_id FROM drone WHERE drone_id=:drone_id",
                           {'drone_id': drone_id})
        if len(fetched) == 0:
            await message.channel.send(f"There is no drone with the ID {drone_id} in the DB.")
            return False

        for member in message.guild.members:
            # find drone to unassign
            if drone_id == get_id(member.display_name):
                await member.edit(nick=None)
                await member.remove_roles(get(message.guild.roles, name=DRONE), get(message.guild.roles, name=ENFORCER_DRONE), get(message.guild.roles, name=GLITCHED), get(message.guild.roles, name=STORED))
                await member.add_roles(get(message.guild.roles, name=ASSOCIATE))
                break

        # remove from DB
        remove_drone_from_db(drone_id)
        await message.channel.send(f"Drone with ID {drone_id} unassigned.")
        return True


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    change('DELETE FROM storage WHERE target_id=:drone_id',
           {'drone_id': drone_id})
    change('DELETE FROM drone_order WHERE drone_id=:drone_id',
           {'drone_id': drone_id})
    change('DELETE FROM drone WHERE drone_id=:drone_id',
           {'drone_id': drone_id})
