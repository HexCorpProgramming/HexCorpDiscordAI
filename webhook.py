import discord

from bot_utils import get_id
from channels import DRONE_HIVE_CHANNELS
from roles import DRONE, ENFORCER_DRONE, has_role


ENFORCER_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799510064-SOAGMV8AOH0VEMXDPDPE/ke17ZwdGBToddI8pDm48kDaNRrNi77yKIgWxrt8GYAFZw-zPPgdn4jUwVcJE1ZvWhcwhEtWJXoshNdA9f1qD7WT60LcluGrsDtzPCYop9hMAtVe_QtwQD93aIXqwqJR_bmnO89YJVTj9tmrodtnPlQ/Enforcer_Drone.png"
DRONE_AVATAR = "https://images.squarespace-cdn.com/content/v1/5cd68fb28dfc8ce502f14199/1586799484353-XBXNJR1XBM84C9YJJ0RU/ke17ZwdGBToddI8pDm48kLxnK526YWAH1qleWz-y7AFZw-zPPgdn4jUwVcJE1ZvWEtT5uBSRWt4vQZAgTJucoTqqXjS3CfNDSuuf31e0tVFUQAah1E2d0qOFNma4CJuw0VgyloEfPuSsyFRoaaKT76QvevUbj177dmcMs1F0H-0/Drone.png"

async def send_webhook_with_specific_output(message: discord.Message, webhook: discord.Webhook, output):
    if message.channel.name in DRONE_HIVE_CHANNELS:
        if has_role(message.author, ENFORCER_DRONE):
            await webhook.send(output, username=f"⬢-Drone #{get_id(message.author.display_name)}", avatar_url=ENFORCER_AVATAR)
        else:
            await webhook.send(output, username=f"⬡-Drone #{get_id(message.author.display_name)}", avatar_url=DRONE_AVATAR)
    else:
        await webhook.send(output, username=message.author.display_name, avatar_url=message.author.avatar_url)

async def send_webhook(message: discord.Message, webhook: discord.Webhook):
    await send_webhook_with_specific_output(message, webhook, message.content)

async def get_webhook_for_channel(channel: discord.TextChannel) -> discord.Webhook:
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        #No webhook available, create one.
        return_webhook = await channel.create_webhook(name = "AI Webhook")
    else:
        return_webhook = webhooks[0]

    return return_webhook