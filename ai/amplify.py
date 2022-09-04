import discord
import id_converter
import webhook
from bot_utils import COMMAND_PREFIX, get_id
from channels import OFFICE
from discord.ext.commands import Cog, command, guild_only
from resources import DRONE_AVATAR
from roles import HIVE_MXTRESS, has_role
from ai.identity_enforcement import identity_enforcable


class AmplificationCog(Cog):

    @guild_only()
    @command(brief=["Hive Mxtress"], usage=f'{COMMAND_PREFIX}amplify "Hello, little drone." #hexcorp-transmissions 9813 3287')
    async def amplify(self, context, message: str, target_channel: discord.TextChannel, *drones):
        '''
        Allows the Hive Mxtress to speak through other drones.
        '''
        member_drones = id_converter.convert_ids_to_members(context.guild, drones) | set(context.message.mentions)

        if not has_role(context.author, HIVE_MXTRESS) or context.channel.name != OFFICE:
            return False

        channel_webhook = await webhook.get_webhook_for_channel(target_channel)

        for drone in member_drones:
            await webhook.proxy_message_by_webhook(message_content=f"{get_id(drone.display_name)} :: {message}",
                                                   message_username=drone.display_name,
                                                   message_avatar=drone.avatar.url if not identity_enforcable(drone, channel=target_channel) else DRONE_AVATAR,
                                                   webhook=channel_webhook)
        return True
