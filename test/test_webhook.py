from src.webhook import webhook_if_message_altered
import unittest
from unittest.mock import ANY, Mock, AsyncMock, patch
from src.ai.data_objects import MessageCopy
import discord
import io


class TestWebhook(unittest.IsolatedAsyncioTestCase):

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_not_proxied_if_message_not_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should do nothing if the message and its copy are identical.
        """

        message_original = Mock()
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.display_avatar.url = "[link to a pretty avatar]"
        message_original.attachments = []

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.display_avatar, message_original.attachments)

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_not_called()
        send_webhook.assert_not_called()

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_content_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message and the message copy are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.display_avatar.url = "[link to a pretty avatar]"
        message_original.reference = None

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.display_avatar)
        message_copy.content = "This is NOT the original message."

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar.url,
                                             message_attachments=[],
                                             channel=message_original.channel,
                                             webhook=None,
                                             embed=None)

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_avatar_url_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message's avatar url and the message copy's avatar_url are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.display_avatar.url = "[link to a pretty avatar]"
        message_original.reference = None

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.display_avatar)
        message_copy.avatar.url = "[link to an even prettier avatar]"

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar.url,
                                             message_attachments=[],
                                             channel=message_original.channel,
                                             webhook=None,
                                             embed=None)

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_display_name_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message's display name and the message copy's display_name are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.display_avatar.url = "[link to a pretty avatar]"
        message_original.reference = None

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.display_avatar)
        message_copy.display_name = "5890 the all powerful droney woney."

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar.url,
                                             message_attachments=[],
                                             channel=message_original.channel,
                                             webhook=None,
                                             embed=None)

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_proxied_with_reference(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy
        the updated version if the original message's display name and the message copy's
        display_name are not identical as well as include an embede pointing to the message
        that is being replied to.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.display_avatar.url = "[link to a pretty avatar]"

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.display_avatar)
        message_copy.display_name = "5890 the all powerful droney woney."

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar.url,
                                             message_attachments=[],
                                             channel=message_original.channel,
                                             webhook=None,
                                             embed=ANY)

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_attachments_are_converted_into_file_objects(self, send_webhook):
        '''
        The webhook_if_message altered function should read each Attachment object in the MessageCopy's attachments attribute
        and convert them into appropriate discord.File objects before passing them to the proxy_message_by_webhook function.

        This is because discord.Message objects have a list of discord.Attachments to represent files,
        but webhooks require discord.File objects.
        '''

        attachment_mock_one = AsyncMock()
        attachment_mock_one.read.return_value = b"Hello world."
        attachment_mock_one.filename = "file1.png"

        attachment_mock_two = AsyncMock()
        attachment_mock_two.read.return_value = b"Hello again, world."
        attachment_mock_two.filename = "file2.png"

        expected_file_one = discord.File(io.BytesIO(b"Hello world."), filename="file1.png")
        expected_file_two = discord.File(io.BytesIO(b"Hello again, world."), filename="file2.png")

        message_original = AsyncMock()
        message_original.channel = "Channel."
        message_original.content = "Content."
        message_original.author.display_name = "Display name"
        message_original.author.display_avatar.url = "Avatar URL"
        message_original.attachments = [attachment_mock_one, attachment_mock_two]

        message_copy = MessageCopy(content=message_original.content, display_name=message_original.author.display_name, avatar=message_original.author.display_avatar, attachments=message_original.attachments)
        message_copy.content = "Altered content."

        await webhook_if_message_altered(message_original, message_copy)

        converted_file_one = send_webhook.call_args.kwargs['message_attachments'][0]
        converted_file_two = send_webhook.call_args.kwargs['message_attachments'][1]

        self.assertEqual(converted_file_one.filename, expected_file_one.filename)
        self.assertEqual(converted_file_two.filename, expected_file_two.filename)

        self.assertEqual(converted_file_one.fp.read(), expected_file_one.fp.read())
        self.assertEqual(converted_file_two.fp.read(), expected_file_two.fp.read())

    @patch("src.webhook.proxy_message_by_webhook")
    async def test_message_avatar_being_set(self, send_webhook):
        """
        The webhook_if_message_altered function should create an embed when replying to a message.
        """

        message_to_reply_to = Mock()
        message_to_reply_to.resolved.content = "This message got replied to"
        message_to_reply_to.resolved.jump_url = "pointing to original message"

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "9813"
        message_original.author.avatar.url = "[link to a pretty avatar]"
        message_original.reference = message_to_reply_to

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.avatar)
        message_copy.avatar.url = "[link to an even prettier avatar]"

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once()
        self.assertEqual(send_webhook.call_args.kwargs['message_content'], message_copy.content)
        self.assertEqual(send_webhook.call_args.kwargs['message_username'], message_copy.display_name)
        self.assertEqual(send_webhook.call_args.kwargs['message_avatar'], message_copy.avatar.url)
        self.assertEqual(send_webhook.call_args.kwargs['message_attachments'], [])
        self.assertEqual(send_webhook.call_args.kwargs['channel'], message_original.channel)
        self.assertEqual(send_webhook.call_args.kwargs['webhook'], None)
        self.assertEqual(send_webhook.call_args.kwargs['embed'].description, "[Reply to](pointing to original message): This message got replied to")
