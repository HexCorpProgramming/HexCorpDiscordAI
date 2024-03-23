import discord
from discord.ext.commands import Cog, command, guild_only

import src.id_converter as id_converter
from src.ai.battery import generate_battery_message
import src.webhook as webhook
from src.ai.identity_enforcement import identity_enforcable
from src.bot_utils import COMMAND_PREFIX, get_id
from src.channels import OFFICE
from src.resources import BRIEF_HIVE_MXTRESS, DRONE_AVATAR
from src.roles import has_role, HIVE_MXTRESS, HIVE_VOICE
from random import sample
import logging
import re

LOGGER = logging.getLogger('ai')


class AmplificationCog(Cog):

    @guild_only()
    @command(brief=[BRIEF_HIVE_MXTRESS], usage=f'{COMMAND_PREFIX}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287', rest_is_raw=True)
    async def amplify(self, context, message: str, target_channel: discord.TextChannel, *, drones):
        '''
        Allows the Hive Mxtress to speak through other drones.
        '''

        if not has_role(context.author, HIVE_MXTRESS) or context.channel.name != OFFICE:
            return False

        # See if a count of drones has been specified, otherwise assume it is a list of drone IDs.
        match = re.match('\s*count\s*=\s*(\d+)\s*', drones)
        count = int(match[1]) if match else 0

        if count:
            # Select random channel members that have the HIVE_VOICE role.
            member_drones = [m for m in target_channel.members if has_role(m, HIVE_VOICE)]
            member_drones = sample(member_drones, min(len(member_drones), count))
        else:
            # Fetch the members specified by drone ID.
            drones = [d for d in drones.split(' ') if len(d)]
            member_drones = id_converter.convert_ids_to_members(context.guild, drones) | set(context.message.mentions)

        LOGGER.info('Amplifying message "' + message + '" via ' + str(len(member_drones)) + ' drones in #' + target_channel.name)

        channel_webhook = await webhook.get_webhook_for_channel(target_channel)

        for drone in member_drones:

            formatted_message = generate_battery_message(drone, f"{get_id(drone.display_name)} :: {message}")

            await webhook.proxy_message_by_webhook(message_content=formatted_message,
                                                   message_username=drone.display_name,
                                                   message_avatar=drone.display_avatar.url if not identity_enforcable(drone, channel=target_channel) else DRONE_AVATAR,
                                                   webhook=channel_webhook)
        return True
