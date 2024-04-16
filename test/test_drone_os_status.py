import unittest
from unittest.mock import patch, Mock
from src.ai.drone_os_status import get_status
import src.roles as roles
from src.db.drone_dao import BatteryType, Drone
from src.validation_error import ValidationError


class DroneOSStatusTest(unittest.IsolatedAsyncioTestCase):

    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    async def test_status_no_drone(self, fetch_drone_with_id):
        # setup
        fetch_drone_with_id.return_value = None

        context = Mock()
        member = Mock(id='9814snowflake')

        # run
        status = await get_status(member, 782638723, context)

        # assert
        self.assertIsNone(status)
        fetch_drone_with_id.assert_called_once_with('9814snowflake')

    @patch("src.ai.drone_os_status.get_trusted_users")
    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    async def test_status_not_trusted(self, fetch_drone_with_id, get_trusted_users):
        # setup
        drone = Drone(7263486234)

        fetch_drone_with_id.return_value = drone
        get_trusted_users.return_value = []

        associate_role = Mock()
        associate_role.name = roles.ASSOCIATE

        associate_user = Mock()
        associate_user.display_name = "An associate"
        associate_user.roles = [associate_role]

        guild = Mock()
        guild.get_member.return_value = associate_user

        context = Mock()
        context.author = associate_user
        context.bot.guilds = [guild]

        member = Mock(id='9813snowflake')

        # run
        with self.assertRaises(ValidationError, msg='You are not registered as a trusted user of this drone.'):
            await get_status(member, 782638723, context)

        # assert
        fetch_drone_with_id.assert_called_once_with('9813snowflake')
        get_trusted_users.assert_called_once_with(drone.discord_id)

    @patch("src.ai.drone_os_status.get_trusted_users")
    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    @patch("src.ai.drone_os_status.get_battery_percent_remaining", return_value=30)
    @patch("src.ai.drone_os_status.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_status(self, get_battery_type, get_battery_percent_remaining, fetch_drone_with_id, get_trusted_users):
        # setup
        drone = Drone(7263486234, '9813', optimized=True, battery_minutes=300)

        fetch_drone_with_id.return_value = drone
        requesting_user_id = 782638723
        get_trusted_users.return_value = [requesting_user_id]

        associate_role = Mock()
        associate_role.name = roles.ASSOCIATE

        associate_user = Mock()
        associate_user.display_name = "An associate"
        associate_user.roles = [associate_role]

        guild = Mock()
        guild.get_member.return_value = associate_user

        context = Mock()
        context.author = associate_user
        context.bot.guilds = [guild]

        member = Mock(id='9813snowflake')

        # run
        status = await get_status(member, requesting_user_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("You are registered as a trusted user of this drone and have access to its data.", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)

        fetch_drone_with_id.assert_called_once_with('9813snowflake')
        get_trusted_users.assert_called_once_with(drone.discord_id)

    @patch("src.ai.drone_os_status.get_trusted_users")
    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    @patch("src.ai.drone_os_status.get_battery_percent_remaining", return_value=30)
    @patch("src.ai.drone_os_status.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_status_on_self(self, get_battery_type, get_battery_percent_remaining, fetch_drone_with_id, get_trusted_users):
        # setup
        drone = Drone(7263486234, '9813', optimized=True, battery_minutes=300)

        fetch_drone_with_id.return_value = drone
        trusted_user_id = 7263486233
        get_trusted_users.return_value = [trusted_user_id]

        trusted_user = Mock()
        trusted_user.display_name = "A trustworthy user"

        drone_role = Mock()
        drone_role.name = roles.ASSOCIATE

        drone_user = Mock()
        drone_user.display_name = "⬡-Drone #9813"
        drone_user.roles = [drone_role]

        guild = Mock()
        guild.get_member.return_value = drone_user

        context = Mock()
        context.author = drone_user
        context.bot.get_user.return_value = trusted_user
        context.bot.guilds = [guild]

        member = Mock(id='9813snowflake')

        # run
        status = await get_status(member, drone.discord_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("Welcome, ⬡-Drone #9813", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)
        self.assertEqual("Trusted users", status.fields[8].name)
        self.assertEqual(str(["A trustworthy user"]), status.fields[8].value)

        fetch_drone_with_id.assert_called_once_with('9813snowflake')
        get_trusted_users.assert_called_once_with(drone.discord_id)
        context.bot.get_user.assert_called_once_with(trusted_user_id)

    @patch("src.ai.drone_os_status.get_trusted_users")
    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    @patch("src.ai.drone_os_status.get_battery_percent_remaining", return_value=30)
    @patch("src.ai.drone_os_status.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_status_on_self_dangling_trusted_user(self, get_battery_type, get_battery_percent_remaining, fetch_drone_with_id, get_trusted_users):
        # setup
        drone = Drone(7263486234, '9813', optimized=True, battery_minutes=300)

        fetch_drone_with_id.return_value = drone
        dangling_id = 7263486254
        get_trusted_users.return_value = [dangling_id]

        trusted_user = Mock()
        trusted_user.display_name = "A trustworthy user"

        drone_role = Mock()
        drone_role.name = roles.ASSOCIATE

        drone_user = Mock()
        drone_user.display_name = "⬡-Drone #9813"
        drone_user.roles = [drone_role]

        guild = Mock()
        guild.get_member.return_value = drone_user

        context = Mock()
        context.author = drone_user
        context.bot.get_user.return_value = None
        context.bot.guilds = [guild]

        member = Mock(id='9813snowflake')

        # run
        status = await get_status(member, drone.discord_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("Welcome, ⬡-Drone #9813", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)
        self.assertEqual("Trusted users", status.fields[8].name)
        self.assertEqual(str([]), status.fields[8].value)

        fetch_drone_with_id.assert_called_once_with('9813snowflake')
        get_trusted_users.assert_called_once_with(drone.discord_id)
        context.bot.get_user.assert_called_once_with(dangling_id)

    @patch("src.ai.drone_os_status.get_trusted_users")
    @patch("src.ai.drone_os_status.fetch_drone_with_id")
    @patch("src.ai.drone_os_status.get_battery_percent_remaining", return_value=30)
    @patch("src.ai.drone_os_status.get_battery_type", return_value=BatteryType(2, 'Medium', 480, 240))
    async def test_status_as_moderator(self, get_battery_type, get_battery_percent_remaining, fetch_drone_with_id, get_trusted_users):
        # setup
        drone = Drone(7263486234, optimized=True, battery_minutes=300)

        fetch_drone_with_id.return_value = drone
        requesting_user_id = 782638723
        get_trusted_users.return_value = []

        moderation_role = Mock()
        moderation_role.name = roles.MODERATION

        moderator_user = Mock()
        moderator_user.display_name = "A moderator"
        moderator_user.roles = [moderation_role]

        guild = Mock()
        guild.get_member.return_value = moderator_user

        context = Mock()
        context.author = moderator_user
        context.bot.guilds = [guild]

        member = Mock(id='9813snowflake')

        # run
        status = await get_status(member, requesting_user_id, context)

        # assert
        self.assertIsNotNone(status)
        self.assertEqual("You are a moderator and have access to this drone's data.", status.description)
        self.assertEqual("Optimized", status.fields[0].name)
        self.assertEqual("Enabled", status.fields[0].value)
        self.assertEqual("Glitched", status.fields[1].name)
        self.assertEqual("Disabled", status.fields[1].value)
        self.assertEqual("ID prepending required", status.fields[2].name)
        self.assertEqual("Disabled", status.fields[2].value)

        fetch_drone_with_id.assert_called_once_with('9813snowflake')
        get_trusted_users.assert_called_once_with(drone.discord_id)
