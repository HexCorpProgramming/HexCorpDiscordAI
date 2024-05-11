import unittest
from unittest.mock import patch
from src.channels import TRANSMISSIONS_CHANNEL, OFFICE
import src.ai.amplify as amplify
from src.bot_utils import COMMAND_PREFIX
from src.roles import HIVE_VOICE
from test.cog import cog
from test.mocks import Mocks


class TestAmplify(unittest.IsolatedAsyncioTestCase):
    '''
    The amplify command...
    '''

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_webhook_called_with_appropriate_message(self, webhook_proxy, mocks: Mocks):
        '''
        Should call proxy_message_by_webhook an amount of times equal to unique drones specified. Each message should be prepended with each drones ID.
        '''

        drone = mocks.drone('3287')
        member = mocks.member('Drone-3287')

        message = mocks.message(mocks.hive_mxtress(), OFFICE, COMMAND_PREFIX + 'amplify "Beep boop!" hex-office 3287')
        mocks.set_drone_members([drone], [member])

        await self.assert_command_successful(message)
        webhook_proxy.assert_called_once_with(
            message_content="3287 :: Beep boop!",
            message_username="Drone-3287",
            message_avatar=member.display_avatar.url,
            webhook=mocks.channel(OFFICE).webhook
        )

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_does_not_work_if_not_mxtress(self, proxy_message, mocks):
        '''
        only works when called by the Hive Mxtress in the Hex Office channel.
        '''

        content = COMMAND_PREFIX + 'amplify "Hello" hex-office 3287'
        initiator = mocks.member()
        target = mocks.member('Drone-3287')
        drone = mocks.drone('3287')

        # In Office, is Mxtress.
        message = mocks.message(mocks.hive_mxtress(), OFFICE, content)
        mocks.set_drone_members([drone], [target])
        await self.assert_command_successful(message)
        proxy_message.assert_called_once()

        # In Office, not Mxtress.
        message = mocks.message(initiator, OFFICE, content)
        mocks.set_drone_members([drone], [target])
        await self.assert_command_error(message)

        # Out of office, is Mxtress
        message = mocks.message(mocks.hive_mxtress(), TRANSMISSIONS_CHANNEL, content)
        mocks.set_drone_members([drone], [target])
        await self.assert_command_error(message)

        # Out of office, not Mxtress.
        message = mocks.message(initiator, TRANSMISSIONS_CHANNEL, content)
        mocks.set_drone_members([drone], [target])
        await self.assert_command_error(message)

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_with_count(self, proxy_message_by_webhook, mocks):
        '''
        Ensure that a count of users can be specified.
        '''

        # The channel members.
        members = [
            mocks.member('Drone-0001'),
            mocks.member('Drone-1234'),
            mocks.member('Drone-5678'),
        ]

        voice_role = mocks.role(HIVE_VOICE)

        # Member 0 doesn't have the voice role and so should not take part in amplification.
        members[1].roles = [voice_role]
        members[2].roles = [voice_role]

        # The drone records for the members that will amplify the message.
        # The first None ends the DroneMember argument converter.
        drones = [
            None,
            mocks.drone('1234'),
            mocks.drone('5678'),
        ]

        mocks.channel('general').members = members

        message = mocks.message(mocks.hive_mxtress(), OFFICE, COMMAND_PREFIX + 'amplify "Beep boop!" general -hive=3')

        # Return the drone records when DroneMember.create is called.
        mocks.set_drone_members(drones, [None])

        await self.assert_command_successful(message)
        self.assertEqual(2, len(proxy_message_by_webhook.mock_calls))

    @patch("src.ai.amplify.webhook.proxy_message_by_webhook")
    @cog(amplify.AmplificationCog)
    async def test_with_non_drone_mention(self, proxy_message_by_webhook, mocks):
        '''
        Ensure that an @mention of a non-drone does not cause an error.
        '''

        message = mocks.message(mocks.hive_mxtress(), OFFICE, COMMAND_PREFIX + 'amplify "Beep boop!" general 3')
        mocks.set_drone_members([None], mocks.member(id=3))

        await self.assert_command_successful(message)
        proxy_message_by_webhook.assert_not_called()
