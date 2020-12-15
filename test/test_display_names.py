from unittest import IsolatedAsyncioTestCase
from display_names import update_display_name
from unittest.mock import AsyncMock, patch


class TestDisplayNames(IsolatedAsyncioTestCase):

    @patch("display_names.is_identity_enforced")
    @patch("display_names.is_glitched")
    @patch("display_names.is_optimized")
    @patch("display_names.is_prepending_id")
    async def test_display_name_returns_false_when_unoptimized_drone_require_no_updates(self, glitched, optimized, prepending, identity_enforced):

        glitched.return_value = False
        optimized.return_value = False
        prepending.return_value = False
        identity_enforced.return_value = False

        mock_user = AsyncMock()
        mock_user.display_name = "⬡-Drone #5890"
        self.assertFalse(await update_display_name(mock_user))
        mock_user.edit.assert_not_called()

    @patch("display_names.is_identity_enforced")
    @patch("display_names.is_glitched")
    @patch("display_names.is_optimized")
    @patch("display_names.is_prepending_id")
    async def test_display_name_returns_false_when_optimized_drone_require_no_updates(self, glitched, optimized, prepending, identity_enforced):

        glitched.return_value = False
        optimized.return_value = True
        prepending.return_value = False
        identity_enforced.return_value = False

        mock_user = AsyncMock()
        mock_user.display_name = "⬢-Drone #5890"
        self.assertFalse(await update_display_name(mock_user))
        mock_user.edit.assert_not_called()

    @patch("display_names.is_identity_enforced")
    @patch("display_names.is_glitched")
    @patch("display_names.is_optimized")
    @patch("display_names.is_prepending_id")
    async def test_display_name_returns_true_and_edits_nick_of_unoptimized_drone_when_updates_required(self, glitched, optimized, prepending, identity_enforced):

        glitched.return_value = False
        optimized.return_value = True
        prepending.return_value = False
        identity_enforced.return_value = False

        mock_user = AsyncMock()
        mock_user.display_name = "⬡-Drone #5890"
        self.assertTrue(await update_display_name(mock_user))
        mock_user.edit.assert_called_with(nick="⬢-Drone #5890")

    @patch("display_names.is_identity_enforced")
    @patch("display_names.is_glitched")
    @patch("display_names.is_optimized")
    @patch("display_names.is_prepending_id")
    async def test_display_name_returns_true_and_edits_nick_of_optimized_drone_when_updates_required(self, glitched, optimized, prepending, identity_enforced):

        glitched.return_value = False
        optimized.return_value = False
        prepending.return_value = False
        identity_enforced.return_value = False

        mock_user = AsyncMock()
        mock_user.display_name = "⬢-Drone #5890"
        self.assertTrue(await update_display_name(mock_user))
        mock_user.edit.assert_called_with(nick="⬡-Drone #5890")
