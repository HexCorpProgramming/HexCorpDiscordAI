import unittest
from unittest.mock import AsyncMock, Mock, patch
from src.channels import OFFICE, TRANSMISSIONS_CHANNEL
import src.ai.amplify as amplify


class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    @patch("src.ai.amplify.generate_battery_message")
    @patch("src.ai.amplify.identity_enforcable", return_value=False)
    @patch("src.ai.amplify.has_role", return_value=True)
    @patch("src.ai.amplify.webhook.get_webhook_for_channel")
    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @patch("src.ai.amplify.fetch_drone_with_id")
    async def test_webhook_called_with_appropriate_message(self, fetch_drone_with_id, webhook_proxy, get_webhook, has_role, identity_enforceable, generate_battery_message):
        '''
        should call proxy_message_by_webhook an amount of times equal to unique drones specified. Each message should be prepended with each drones ID.
        '''
        bot = AsyncMock()
        bot.add_command = Mock()
        amplification_cog = amplify.AmplificationCog()
        amplification_cog = amplification_cog._inject(bot)

        member = AsyncMock()
        member.display_avatar.url = "Pretty avatar"
        member.display_name = "3287"

        webhook = AsyncMock()
        get_webhook.return_value = webhook

        context = AsyncMock()
        context.message.mentions = [member]
        context.channel.name = OFFICE
        message = "Beep boop!"
        target_channel = AsyncMock()

        generate_battery_message.side_effect = lambda drone, msg: msg

        drone = Mock()
        drone.drone_id = 3287
        fetch_drone_with_id.return_value = drone

        await amplification_cog.amplify(context, message, target_channel, members=[member])
        webhook_proxy.assert_called_once_with(
            message_content="3287 :: Beep boop!",
            message_username="3287",
            message_avatar="Pretty avatar",
            webhook=webhook
        )

        generate_battery_message.assert_called_once_with(drone, "3287 :: Beep boop!")

    @patch("src.ai.amplify.has_role")
    async def test_does_not_work_if_not_Mxtress(self, has_role):
        '''
        only works when called by the Hive Mxtress in the Hex Office channel.
        '''
        bot = AsyncMock()
        bot.add_command = Mock()
        amplification_cog = amplify.AmplificationCog()
        amplification_cog = amplification_cog._inject(bot)

        context = AsyncMock()
        context.channel.name = OFFICE

        # In Office, is Mxtress.
        has_role.return_value = True
        self.assertTrue(await amplification_cog.amplify(context, "Hello world", AsyncMock(), members=[]))

        # In Office, not Mxtress.
        has_role.return_value = False
        self.assertFalse(await amplification_cog.amplify(context, "Hello world", AsyncMock(), members=[]))

        context.channel.name = TRANSMISSIONS_CHANNEL

        # Out of office, is Mxtress
        has_role.return_value = True
        self.assertFalse(await amplification_cog.amplify(context, "Hello world", AsyncMock(), members=[]))

        # Out of office, not Mxtress.
        has_role.return_value = False
        self.assertFalse(await amplification_cog.amplify(context, "Hello world", AsyncMock(), members=[]))

    @patch("src.ai.amplify.has_role")
    @patch("src.ai.amplify.webhook.get_webhook_for_channel")
    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @patch("src.ai.amplify.generate_battery_message")
    @patch("src.ai.amplify.identity_enforcable")
    @patch("src.ai.amplify.fetch_drone_with_id")
    async def test_with_count(self, fetch_drone_with_id, identity_enforcable, generate_battery_message, proxy_message_by_webhook, get_webhook_for_channel, has_role):
        '''
        Ensure that a count of users can be specified.
        '''

        bot = AsyncMock()
        bot.add_command = Mock()
        amplification_cog = amplify.AmplificationCog()
        amplification_cog = amplification_cog._inject(bot)

        context = AsyncMock()
        context.channel.name = OFFICE

        # The channel to which the message will be sent.
        target_channel = Mock()
        target_channel.members = [Mock(), Mock(), Mock()]
        target_channel.name = 'general'

        # The drones that will amplify the message.
        target_channel.members[0].display_name = '1234'
        target_channel.members[1].display_name = '5678'

        # Give only two channel members out of three have the required role.
        has_role.side_effect = [True, True, True, False]

        # Mock helper functions to return what they were passed.
        generate_battery_message.side_effect = lambda a, b: b

        identity_enforcable.return_value = False

        # The drones to be looked up from the members.
        drones = [Mock(), Mock()]
        drones[0].drone_id = 1234
        drones[1].drone_id = 5678
        fetch_drone_with_id.side_effect = drones

        self.assertTrue(await amplification_cog.amplify(context, "Hello world", target_channel, members=[], count=3))
        self.assertEqual(2, len(proxy_message_by_webhook.mock_calls))

    @patch("src.ai.amplify.has_role")
    @patch("src.ai.amplify.webhook.get_webhook_for_channel")
    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @patch("src.ai.amplify.generate_battery_message")
    @patch("src.ai.amplify.identity_enforcable")
    @patch("src.ai.amplify.fetch_drone_with_id")
    async def test_with_non_drone_mention(self, fetch_drone_with_id, identity_enforcable, generate_battery_message, proxy_message_by_webhook, get_webhook_for_channel, has_role):
        '''
        Ensure that an @mention of a non-drone does not cause an error.
        '''

        bot = AsyncMock()
        bot.add_command = Mock()
        amplification_cog = amplify.AmplificationCog()
        amplification_cog = amplification_cog._inject(bot)

        context = AsyncMock()
        context.channel.name = OFFICE

        # The channel to which the message will be sent.
        target_channel = Mock()
        target_channel.members = [Mock()]
        target_channel.name = 'general'

        # The @mentioned member.
        member = Mock()

        # The member is not a drone.
        fetch_drone_with_id.return_value = None

        # Mock helper functions to return what they were passed.
        generate_battery_message.side_effect = lambda a, b: b

        identity_enforcable.return_value = False

        self.assertTrue(await amplification_cog.amplify(context, "Hello world", target_channel, members=[member]))
