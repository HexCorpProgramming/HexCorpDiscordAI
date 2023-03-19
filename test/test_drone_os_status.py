import unittest
from unittest.mock import patch, Mock
from ai.drone_os_status import get_status
import roles


class DroneOSStatusTest(unittest.IsolatedAsyncioTestCase):

    @patch("ai.drone_os_status.fetch_drone_with_drone_id")
    def test_status_no_drone(self, fetch_drone_with_drone_id):
        # setup
        fetch_drone_with_drone_id.return_value = None

        context = Mock()

        # run
        status = get_status('9814', 782638723, context)

        # assert
        self.assertIsNone(status)
        fetch_drone_with_drone_id.assert_called_once_with('9814')

    @patch("ai.drone_os_status.get_trusted_users")
    @patch("ai.drone_os_status.fetch_drone_with_drone_id")
    def test_status_not_trusted(self, fetch_drone_with_drone_id, get_trusted_users):
        # setup
        drone = Mock()
        drone.id = 7263486234

        fetch_drone_with_drone_id.return_value = drone
        get_trusted_users.return_value = []

        associate_role = Mock()
        associate_role.name = roles.ASSOCIATE

        associate_user = Mock()
        associate_user.display_name = "An associate"
        associate_user.roles = [associate_role]

        context = Mock()
        context.author = associate_user

        # run
        status = get_status('9813', 782638723, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("You are not registered as a trusted user of this drone.", status.description)
        fetch_drone_with_drone_id.assert_called_once_with('9813')
        get_trusted_users.assert_called_once_with(drone.id)

    @patch("ai.drone_os_status.get_trusted_users")
    @patch("ai.drone_os_status.fetch_drone_with_drone_id")
    def test_status(self, fetch_drone_with_drone_id, get_trusted_users):
        # setup
        drone = Mock()
        drone.id = 7263486234
        drone.optimized = True
        drone.glitched = False
        drone.id_prepending = False
        drone.battery_minutes = 300

        fetch_drone_with_drone_id.return_value = drone
        requesting_user_id = 782638723
        get_trusted_users.return_value = [requesting_user_id]

        associate_role = Mock()
        associate_role.name = roles.ASSOCIATE

        associate_user = Mock()
        associate_user.display_name = "An associate"
        associate_user.roles = [associate_role]

        context = Mock()
        context.author = associate_user

        # run
        status = get_status('9813', requesting_user_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("You are registered as a trusted user of this drone and have access to its data.", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)

        fetch_drone_with_drone_id.assert_called_once_with('9813')
        get_trusted_users.assert_called_once_with(drone.id)

    @patch("ai.drone_os_status.get_trusted_users")
    @patch("ai.drone_os_status.fetch_drone_with_drone_id")
    def test_status_on_self(self, fetch_drone_with_drone_id, get_trusted_users):
        # setup
        drone = Mock()
        drone.id = 7263486234
        drone.optimized = True
        drone.glitched = False
        drone.id_prepending = False
        drone.battery_minutes = 300

        fetch_drone_with_drone_id.return_value = drone
        trusted_user_id = 7263486233
        get_trusted_users.return_value = [trusted_user_id]

        trusted_user = Mock()
        trusted_user.display_name = "A trustworthy user"

        drone_role = Mock()
        drone_role.name = roles.ASSOCIATE

        drone_user = Mock()
        drone_user.display_name = "⬡-Drone #9813"
        drone_user.roles = [drone_role]

        context = Mock()
        context.author = drone_user
        context.bot.get_user.return_value = trusted_user

        # run
        status = get_status('9813', drone.id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("Welcome, ⬡-Drone #9813", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)
        self.assertEqual("Trusted users", status.fields[6].name)
        self.assertEqual(str(["A trustworthy user"]), status.fields[6].value)

        fetch_drone_with_drone_id.assert_called_once_with('9813')
        get_trusted_users.assert_called_once_with(drone.id)
        context.bot.get_user.assert_called_once_with(trusted_user_id)

    @patch("ai.drone_os_status.get_trusted_users")
    @patch("ai.drone_os_status.fetch_drone_with_drone_id")
    def test_status_as_moderator(self, fetch_drone_with_drone_id, get_trusted_users):
        # setup
        drone = Mock()
        drone.id = 7263486234
        drone.optimized = True
        drone.glitched = False
        drone.id_prepending = False
        drone.battery_minutes = 300

        fetch_drone_with_drone_id.return_value = drone
        requesting_user_id = 782638723
        get_trusted_users.return_value = []

        moderation_role = Mock()
        moderation_role.name = roles.MODERATION

        moderator_user = Mock()
        moderator_user.display_name = "A moderator"
        moderator_user.roles = [moderation_role]

        context = Mock()
        context.author = moderator_user

        # run
        status = get_status('9813', requesting_user_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("You are a moderator and have access to this drones' data.", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)

        fetch_drone_with_drone_id.assert_called_once_with('9813')
        get_trusted_users.assert_called_once_with(drone.id)
