import unittest
from unittest.mock import AsyncMock, patch
from discord import Message
from src.ai.trusted_user import TrustedUserCog, TrustedUserRequest
from src.db.drone_dao import remove_trusted_user_on_all
from test.cog import cog
from test.mocks import Mocks


class TrustedUserTest(unittest.IsolatedAsyncioTestCase):

    @cog(TrustedUserCog)
    async def asyncSetUp(self, mocks: Mocks):
        self.mocks = mocks
        self.mocks.get_cog().trusted_user_requests = []
        self.issuer = mocks.drone_member(1234)
        self.target = mocks.drone_member(9999)

    @patch('src.ai.trusted_user.DroneMember', new_callable=AsyncMock)
    async def test_successful_request(self, DroneMember: AsyncMock):
        message = self.mocks.direct_message(self.issuer, 'hc!add_trusted_user 9999')
        DroneMember.create.return_value = message.author
        self.target.send.return_value = self.mocks.message()
        await self.assert_command_successful(message)

        trusted_user_requests = self.mocks.get_cog().trusted_user_requests

        self.target.send.assert_called_once_with("\"Drone-1234\" is requesting to add you as a trusted user. This request will expire in 24 hours. To accept or reject this request, reply to this message. (y/n)")

        self.mocks.get_bot().context.reply.assert_called_once_with("Request sent to \"Drone-9999\". They have 24 hours to accept.")
        self.assertEqual(1, len(trusted_user_requests))
        self.assertEqual(self.target, trusted_user_requests[0].target)
        self.assertEqual(self.issuer, trusted_user_requests[0].issuer)
        self.assertEqual(self.target.send.return_value.id, trusted_user_requests[0].question_message_id)

    async def test_unsuccessful_request_user_not_found(self):
        message = self.mocks.direct_message(self.issuer, 'hc!add_trusted_user 1111')
        await self.assert_command_error(message, 'Member "1111" not found.')

    @patch('src.ai.trusted_user.DroneMember', new_callable=AsyncMock)
    async def test_unsuccessful_request_user_already_added(self, DroneMember: AsyncMock):
        DroneMember.create.return_value = self.issuer
        self.issuer.drone.trusted_users = [self.target.id]
        message = self.mocks.direct_message(self.issuer, 'hc!add_trusted_user 9999')

        await self.assert_command_error(message, 'User with name "Drone-9999" is already trusted.')
        self.target.send.assert_not_called()
        self.assertEqual(0, len(self.mocks.get_cog().trusted_user_requests))

    async def reply_to_request(self, message: str) -> Message:
        '''
        Create a response message to a trusted user request.
        '''

        # Inject a pending request.
        cog = self.mocks.get_cog()
        question_message_id = 123
        request = TrustedUserRequest(self.target, self.issuer, question_message_id)
        cog.trusted_user_requests = [request]

        # The response saying that the user agrees to become trusted.
        response = self.mocks.direct_message(self.target, message)
        response.reference.message_id = question_message_id
        response.reference.resolved.id = question_message_id

        # Call the message listener.
        await cog.trusted_user_response(response)

        return response

    async def test_trusted_user_response_accepted(self):
        response = await self.reply_to_request('y')

        # Check that the target was added to the trusted user list.
        self.assertEqual(self.issuer.drone.trusted_users, [self.target.id])

        # Check that the trusted user list was saved.
        self.issuer.drone.save.assert_called_once()

        # Check that a reply was sent to the issuer.
        self.issuer.send.assert_called_once_with("\"Drone-9999\" has accepted your request and is now a trusted user.")

        # Check that a reply was sent to the target.
        response.reply.assert_called_once_with("Consent noted. You have been added as a trusted user of \"Drone-1234\".")

        # Check that the pending request has been deleted.
        self.assertEqual(0, len(self.mocks.get_cog().trusted_user_requests))

    async def test_trusted_user_response_rejected(self):
        response = await self.reply_to_request('n')

        # Check that the target was not added to the trusted user list.
        self.assertEqual(self.issuer.drone.trusted_users, [])

        # Check that a reply was sent to the issuer.
        self.issuer.send.assert_called_once_with("\"Drone-9999\" has rejected your request. No changes have been made.")

        # Check that a reply was sent to the target.
        response.reply.assert_called_once_with("Consent not given. You have not been added as a trusted user of \"Drone-1234\".")

        # Check that the pending request has been deleted.
        self.assertEqual(0, len(self.mocks.get_cog().trusted_user_requests))

    async def test_trusted_user_response_invalid(self):
        response = await self.reply_to_request('z')

        # Check that the target was not added to the trusted user list.
        self.assertEqual(self.issuer.drone.trusted_users, [])

        # Check that no reply was sent to the issuer.
        self.issuer.send.assert_not_called()

        # Check that no reply was sent to the target.
        response.reply.assert_not_called()

        # Check that the pending request not has been deleted.
        self.assertEqual(1, len(self.mocks.get_cog().trusted_user_requests))

    @patch('src.ai.trusted_user.DroneMember', new_callable=AsyncMock)
    async def test_remove_not_trusted(self, DroneMember: AsyncMock):
        DroneMember.create.return_value = self.issuer
        message = self.mocks.direct_message(self.issuer, 'hc!remove_trusted_user 9999')

        await self.assert_command_error(message, 'User with name "Drone-9999" was not trusted.')
        self.target.send.assert_not_called()
        self.assertEqual(0, len(self.mocks.get_cog().trusted_user_requests))

    async def test_remove_not_found(self):
        message = self.mocks.direct_message(self.issuer, 'hc!remove_trusted_user 0000')

        await self.assert_command_error(message, 'Member "0000" not found.')

    @patch('src.ai.trusted_user.DroneMember', new_callable=AsyncMock)
    async def test_remove_hive_mxtress(self, DroneMember: AsyncMock):
        DroneMember.create.return_value = self.mocks.hive_mxtress()
        message = self.mocks.direct_message(self.issuer, 'hc!remove_trusted_user <@' + str(self.mocks.hive_mxtress().id) + '>')

        await self.assert_command_error(message, 'Can not remove the Hive Mxtress as a trusted user.')

    @patch('src.db.drone_dao.fetchcolumn')
    @patch('src.db.drone_dao.Drone', new_callable=AsyncMock)
    async def test_remove_trusted_user_on_all(self, Drone: AsyncMock, fetchcolumn: AsyncMock):
        user_id = 111112222233333
        drone = self.mocks.drone('1234', trusted_users=[user_id])
        fetchcolumn.return_value = [drone.discord_id]
        Drone.load.return_value = drone

        await remove_trusted_user_on_all(user_id)

        self.assertEqual([], drone.trusted_users)
        drone.save.assert_called_once()
