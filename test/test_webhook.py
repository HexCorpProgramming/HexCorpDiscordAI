from webhook import webhook_if_message_altered
import unittest
from unittest.mock import Mock, AsyncMock, patch
from db.data_objects import MessageCopy


class TestWebhook(unittest.IsolatedAsyncioTestCase):

    @patch("webhook.proxy_message_by_webhook")
    async def test_message_not_proxied_if_message_not_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should do nothing if the message and its copy are identical.
        """

        message_original = Mock()
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.avatar_url = "[link to a pretty avatar]"

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.avatar_url)

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_not_called()
        send_webhook.assert_not_called()

    @patch("webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_content_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message and the message copy are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.avatar_url = "[link to a pretty avatar]"

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.avatar_url)
        message_copy.content = "This is NOT the original message."

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar_url,
                                             channel=message_original.channel,
                                             webhook=None)

    @patch("webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_avatar_url_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message's avatar url and the message copy's avatar_url are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.avatar_url = "[link to a pretty avatar]"

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.avatar_url)
        message_copy.avatar_url = "[link to an even prettier avatar]"

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar_url,
                                             channel=message_original.channel,
                                             webhook=None)

    @patch("webhook.proxy_message_by_webhook")
    async def test_message_proxied_if_message_display_name_altered(self, send_webhook):
        """
        The webhook_if_message_altered function should delete the original message and proxy the updated version if the original message's display name and the message copy's display_name are not identical.
        """

        message_original = AsyncMock()
        message_original.channel = "Some channel"
        message_original.content = "Beep boop."
        message_original.author.display_name = "5890"
        message_original.author.avatar_url = "[link to a pretty avatar]"

        message_copy = MessageCopy(message_original.content, message_original.author.display_name, message_original.author.avatar_url)
        message_copy.display_name = "5890 the all powerful droney woney."

        await webhook_if_message_altered(message_original, message_copy)

        message_original.delete.assert_called_once()
        send_webhook.assert_called_once_with(message_content=message_copy.content,
                                             message_username=message_copy.display_name,
                                             message_avatar=message_copy.avatar_url,
                                             channel=message_original.channel,
                                             webhook=None)
