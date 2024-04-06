import unittest
from unittest.mock import AsyncMock, patch
from src.channels import TRANSMISSIONS_CHANNEL, OFFICE
import src.ai.amplify as amplify
from test.utils import assert_command_error, assert_command_successful, cog
from src.bot_utils import COMMAND_PREFIX


class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    @patch("src.ai.amplify.generate_battery_message")
    @patch("src.ai.amplify.identity_enforcable", return_value=False)
    @patch("src.bot_utils.has_role", return_value=True)
    @patch("src.ai.amplify.webhook.get_webhook_for_channel")
    @patch("src.ai.amplify.id_converter.convert_ids_to_members")
    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_webhook_called_with_appropriate_message(self, webhook_proxy, id_converter, get_webhook, has_role, identity_enforceable, generate_battery_message, bot):
        '''
        should call proxy_message_by_webhook an amount of times equal to unique drones specified. Each message should be prepended with each drones ID.
        '''

        drone = AsyncMock()
        drone.display_avatar.url = "Pretty avatar"
        drone.display_name = "3287"
        id_converter.return_value = set(drone)

        webhook = AsyncMock()
        get_webhook.return_value = webhook

        message = bot.create_message(OFFICE, COMMAND_PREFIX + 'amplify "Beep boop!" hex-office 3287', mentions=[drone])

        generate_battery_message.return_value = "3287 :: Beep boop!"

        await assert_command_successful(bot, message)
        webhook_proxy.assert_called_once_with(
            message_content="3287 :: Beep boop!",
            message_username="3287",
            message_avatar="Pretty avatar",
            webhook=webhook
        )

        generate_battery_message.assert_called_once_with(drone, "3287 :: Beep boop!")

    @patch("src.bot_utils.has_role")
    @patch("src.ai.amplify.id_converter", new_callable=AsyncMock)
    @cog(amplify.AmplificationCog)
    async def test_does_not_work_if_not_Mxtress(self, id_converter, has_role, bot):
        '''
        only works when called by the Hive Mxtress in the Hex Office channel.
        '''

        message = bot.create_message(OFFICE, COMMAND_PREFIX + 'amplify "Hello" hex-office 3287')

        # In Office, is Mxtress.
        has_role.return_value = True
        await assert_command_successful(bot, message)
        id_converter.convert_ids_to_members.assert_called_once()

        # In Office, not Mxtress.
        has_role.return_value = False
        await assert_command_error(bot, message)

        message.channel.name = TRANSMISSIONS_CHANNEL

        # Out of office, is Mxtress
        has_role.return_value = True
        await assert_command_error(bot, message)

        # Out of office, not Mxtress.
        has_role.return_value = False
        await assert_command_error(bot, message)
