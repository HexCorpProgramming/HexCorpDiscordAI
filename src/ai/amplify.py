import discord
from discord.ext.commands import Cog, Greedy


from typing import Optional
from src.ai.commands import NamedParameterConverter
from src.ai.battery import generate_battery_message
import src.webhook as webhook
from src.bot_utils import channels_only, command, COMMAND_PREFIX, hive_mxtress_only
from src.channels import OFFICE
from src.roles import has_role, HIVE_VOICE
from random import sample
from src.log import log
from src.drone_member import DroneMember


class AmplificationCog(Cog):

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287', rest_is_raw=True)
    async def amplify(self, context, message: str, target_channel: discord.TextChannel, members: Greedy[DroneMember], count: Optional[NamedParameterConverter('hive', int)] = 0):  # noqa: F821

        '''
        Allows the Hive Mxtress to speak through other drones.
        '''

        if count:
            # Select random channel members that have the HIVE_VOICE role.
            members = [m for m in target_channel.members if has_role(m, HIVE_VOICE)]
            members = sample(members, min(len(members), count))

            # Convert Members to DroneMembers.
            members = [await DroneMember.create(m) for m in members]

        log.info('Amplifying message "' + message + '" via ' + str(len(members)) + ' drones in #' + target_channel.name)

        channel_webhook = await webhook.get_webhook_for_channel(target_channel)

        for member in members:

            if member.drone is None:
                continue

            formatted_message = await generate_battery_message(member, f"{member.drone.drone_id} :: {message}")

            await webhook.proxy_message_by_webhook(message_content=formatted_message,
                                                   message_username=member.display_name,
                                                   message_avatar=member.avatar_url(target_channel),
                                                   webhook=channel_webhook)
        return True
