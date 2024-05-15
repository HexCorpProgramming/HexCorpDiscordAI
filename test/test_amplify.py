import unittest
from unittest.mock import AsyncMock, patch
from src.channels import TRANSMISSIONS_CHANNEL, OFFICE
import src.ai.amplify as amplify
from src.roles import HIVE_VOICE
from test.cog import cog
from test.mocks import Mocks


class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_webhook_called_with_appropriate_message(self, webhook_proxy: AsyncMock, mocks: Mocks):
        '''
        Should call proxy_message_by_webhook an amount of times equal to unique drones specified. Each message should be prepended with each drones ID.
        '''

        drone_member = mocks.drone_member(3287)
        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'amplify "Beep boop!" hex-office 3287')

        await self.assert_command_successful(message)
        webhook_proxy.assert_called_once_with(
            message_content="3287 :: Beep boop!",
            message_username="Drone-3287",
            message_avatar=drone_member._avatar,
            webhook=mocks.channel(OFFICE).webhook
        )

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_does_not_work_if_not_mxtress(self, proxy_message: AsyncMock, mocks: Mocks):
        '''
        only works when called by the Hive Mxtress in the Hex Office channel.
        '''

        content = 'amplify "Hello" hex-office 3287'
        mocks.drone_member(3287)
        initiator = mocks.member()

        # In Office, is Mxtress.
        message = mocks.command(mocks.hive_mxtress(), OFFICE, content)
        await self.assert_command_successful(message)
        proxy_message.assert_called_once()

        # In Office, not Mxtress.
        message = mocks.command(initiator, OFFICE, content)
        await self.assert_command_error(message)

        # Out of office, is Mxtress
        message = mocks.command(mocks.hive_mxtress(), TRANSMISSIONS_CHANNEL, content)
        await self.assert_command_error(message)

        # Out of office, not Mxtress.
        message = mocks.command(initiator, TRANSMISSIONS_CHANNEL, content)
        await self.assert_command_error(message)

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @patch("src.ai.amplify.DroneMember", new_callable=AsyncMock)
    @cog(amplify.AmplificationCog)
    async def test_with_count(self, DroneMember, proxy_message_by_webhook, mocks):
        '''
        Ensure that a count of users can be specified.
        '''

        # The channel members.
        # Drone 0001 doesn't have the voice role and so should not take part in amplification.
        members = [
            mocks.member('Drone-0001'),
            mocks.member('Drone-1234', roles=[HIVE_VOICE]),
            mocks.member('Drone-5678', roles=[HIVE_VOICE]),
        ]

        # The drone records for the members that will amplify the message.
        # The first None ends the DroneMember argument converter.
        DroneMember.create.side_effect = [mocks.drone_member('1234'), mocks.drone_member('5678')]

        mocks.channel('general').members = members

        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'amplify "Beep boop!" general -hive=3')

        await self.assert_command_successful(message)
        self.assertEqual(2, len(proxy_message_by_webhook.mock_calls))

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_with_non_drone_mention(self, proxy_message_by_webhook, mocks):
        '''
        Ensure that an @mention of a non-drone does not cause an error.
        '''

        message = mocks.command(mocks.hive_mxtress(), OFFICE, 'amplify "Beep boop!" general 3')
        mocks.member(id=3)

        await self.assert_command_successful(message)
        proxy_message_by_webhook.assert_not_called()
