import logging
import re

import discord
from discord.ext import commands
from discord.utils import get

from channels import OFFICE
from roles import DRONE, ENFORCER_DRONE, GLITCHED, STORED, HIVE_MXTRESS, ASSOCIATE, has_role

from db.drone import delete_drone_by_drone_id, fetch_drone_with_drone_id
from db.drone_order import delete_drone_order_by_drone_id
from db.storage import delete_storage_by_target_id
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
        drone = fetch_drone_with_drone_id(drone_id)
        # check for existence
        if drone is None:
            await message.channel.send(f"There is no drone with the ID {drone_id} in the DB.")
            return False

        member = self.bot.guilds[0].get_member(drone.id)
        await member.edit(nick=None)
        await member.remove_roles(get(message.guild.roles, name=DRONE), get(message.guild.roles, name=ENFORCER_DRONE), get(message.guild.roles, name=GLITCHED), get(message.guild.roles, name=STORED))
        await member.add_roles(get(message.guild.roles, name=ASSOCIATE))

        # remove from DB
        remove_drone_from_db(drone_id)
        await message.channel.send(f"Drone with ID {drone_id} unassigned.")
        return True


def remove_drone_from_db(drone_id: str):
    # delete all references and then the actual drone entry
    delete_drone_order_by_drone_id(drone_id)
    delete_storage_by_target_id(drone_id)
    delete_drone_by_drone_id(drone_id)
