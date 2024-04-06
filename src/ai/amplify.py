import discord
from discord.ext.commands import Cog, command, Greedy, guild_only


from typing import Optional, Union
from src.ai.commands import DroneMemberConverter, NamedParameterConverter
from src.ai.battery import generate_battery_message
import src.webhook as webhook
from src.ai.identity_enforcement import identity_enforcable
from src.bot_utils import channels_only, command, COMMAND_PREFIX, hive_mxtress_only
from src.channels import OFFICE
from src.resources import DRONE_AVATAR
from src.db.drone_dao import fetch_drone_with_id
from src.roles import has_role, HIVE_VOICE
from random import sample
import logging

LOGGER = logging.getLogger('ai')


class AmplificationCog(Cog):

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287', rest_is_raw=True)
    async def amplify(self, context, message: str, target_channel: discord.TextChannel, members: Greedy[Union[discord.Member, DroneMemberConverter]], count: Optional[NamedParameterConverter('hive', int)] = 0):  # noqa: F821

        '''
        Allows the Hive Mxtress to speak through other drones.
        '''

        if count:
            # Select random channel members that have the HIVE_VOICE role.
            members = [m for m in target_channel.members if has_role(m, HIVE_VOICE)]
            members = sample(members, min(len(members), count))

        LOGGER.info('Amplifying message "' + message + '" via ' + str(len(members)) + ' drones in #' + target_channel.name)

        channel_webhook = await webhook.get_webhook_for_channel(target_channel)

        for member in members:

            drone = fetch_drone_with_id(discord_id=member.id)

            if drone is None:
                continue

            formatted_message = generate_battery_message(drone, f"{drone.drone_id} :: {message}")

            await webhook.proxy_message_by_webhook(message_content=formatted_message,
                                                   message_username=member.display_name,
                                                   message_avatar=member.display_avatar.url if not await identity_enforcable(member, channel=target_channel) else DRONE_AVATAR,
                                                   webhook=channel_webhook)
        return True
