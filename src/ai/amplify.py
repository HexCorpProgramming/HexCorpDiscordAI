import discord
from discord.ext.commands import Cog

import src.id_converter as id_converter
from src.ai.battery import generate_battery_message
import src.webhook as webhook
from src.ai.identity_enforcement import identity_enforcable
from src.bot_utils import channels_only, command, COMMAND_PREFIX, get_id, hive_mxtress_only
from src.channels import OFFICE
from src.resources import DRONE_AVATAR


class AmplificationCog(Cog):

    @channels_only(OFFICE)
    @hive_mxtress_only()
    @command(usage=f'{COMMAND_PREFIX}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287')
    async def amplify(self, context, message: str, target_channel: discord.TextChannel, *drones):
        '''
        Allows the Hive Mxtress to speak through other drones.
        '''
        member_drones = await id_converter.convert_ids_to_members(context.guild, drones) | set(context.message.mentions)

        channel_webhook = await webhook.get_webhook_for_channel(target_channel)

        for drone in member_drones:

            formatted_message = await generate_battery_message(drone, f"{get_id(drone.display_name)} :: {message}")

            await webhook.proxy_message_by_webhook(message_content=formatted_message,
                                                   message_username=drone.display_name,
                                                   message_avatar=drone.display_avatar.url if not await identity_enforcable(drone, channel=target_channel) else DRONE_AVATAR,
                                                   webhook=channel_webhook)
        return True
