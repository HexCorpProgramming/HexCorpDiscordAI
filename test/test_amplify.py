import unittest
from unittest.mock import AsyncMock, patch
from channels import OFFICE, TRANSMISSIONS_CHANNEL
import ai.amplify as amplify


class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    @patch("ai.amplify.generate_battery_message")
    @patch("ai.amplify.identity_enforcable", return_value=False)
    @patch("ai.amplify.has_role", return_value=True)
    @patch("ai.amplify.webhook.get_webhook_for_channel")
    @patch("ai.amplify.id_converter.convert_ids_to_members")
    @patch("ai.amplify.webhook.proxy_message_by_webhook")
    async def test_webhook_called_with_appropriate_message(self, webhook_proxy, id_converter, get_webhook, has_role, identity_enforceable, generate_battery_message):
        '''
        should call proxy_message_by_webhook an amount of times equal to unique drones specified. Each message should be prepended with each drones ID.
        '''
        amplification_cog = amplify.AmplificationCog()

        drone = AsyncMock()
        drone.display_avatar.url = "Pretty avatar"
        drone.display_name = "3287"
        id_converter.return_value = set(drone)

        webhook = AsyncMock()
        get_webhook.return_value = webhook

        context = AsyncMock()
        context.message.mentions = [drone]
        context.channel.name = OFFICE
        message = "Beep boop!"
        target_channel = AsyncMock()

        generate_battery_message.return_value = "3287 :: Beep boop!"

        await amplification_cog.amplify(amplification_cog, context, message, target_channel)
        webhook_proxy.assert_called_once_with(
            message_content="3287 :: Beep boop!",
            message_username="3287",
            message_avatar="Pretty avatar",
            webhook=webhook
        )

        generate_battery_message.assert_called_once_with("3287 :: Beep boop!")

    @patch("ai.amplify.has_role")
    async def test_does_not_work_if_not_Mxtress(self, has_role):
        '''
        only works when called by the Hive Mxtress in the Hex Office channel.
        '''
        amplification_cog = amplify.AmplificationCog()

        context = AsyncMock()
        context.channel.name = OFFICE

        # In Office, is Mxtress.
        has_role.return_value = True
        self.assertTrue(await amplification_cog.amplify(amplification_cog, context, "Hello world", AsyncMock()))

        # In Office, not Mxtress.
        has_role.return_value = False
        self.assertFalse(await amplification_cog.amplify(amplification_cog, context, "Hello world", AsyncMock()))

        context.channel.name = TRANSMISSIONS_CHANNEL

        # Out of office, is Mxtress
        has_role.return_value = True
        self.assertFalse(await amplification_cog.amplify(amplification_cog, context, "Hello world", AsyncMock()))

        # Out of office, not Mxtress.
        has_role.return_value = False
        self.assertFalse(await amplification_cog.amplify(amplification_cog, context, "Hello world", AsyncMock()))
