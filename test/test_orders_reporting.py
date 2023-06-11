import unittest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timedelta
from uuid import uuid4

import src.roles as roles
import src.channels as channels
import src.ai.orders_reporting as orders_reporting
from src.db.data_objects import DroneOrder
import test.test_utils as test_utils

drone_role = Mock()
drone_role.name = roles.DRONE

associate_role = Mock()
associate_role.name = roles.ASSOCIATE

orders_reporting_channel = AsyncMock()
orders_reporting_channel.name = channels.ORDERS_REPORTING

bot = AsyncMock()
bot.guilds[0].roles = [drone_role, associate_role]
bot.guilds[0].channels = [orders_reporting_channel]


class OrdersReportingTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        bot.reset_mock()
        orders_reporting_channel.reset_mock()

    @patch("src.ai.orders_reporting.convert_id_to_member")
    @patch("src.ai.orders_reporting.delete_drone_order")
    @patch("src.ai.orders_reporting.fetch_all_drone_orders", return_value=[DroneOrder('mocked_order_id', '5890', 'beep booping', str(datetime.now() + timedelta(minutes=-1)))])
    async def test_check_for_completed_orders_completed(self, fetch_all_drone_orders, delete_drone_order, convert_id_to_member):
        # setup
        activated_member = AsyncMock()
        activated_member.id = '5890snowflake'
        activated_member.mention = '<5890mention>'

        convert_id_to_member.return_value = activated_member

        orders_reporting_cog = orders_reporting.OrderReportingCog(bot)

        # run
        await test_utils.start_and_await_loop(orders_reporting_cog.deactivate_drones_with_completed_orders)

        # assert
        convert_id_to_member.assert_called_once_with(bot.guilds[0], '5890')
        delete_drone_order.assert_called_once_with('mocked_order_id')
        orders_reporting_channel.send.assert_called_once_with('<5890mention> Drone 5890 Deactivate.\nDrone 5890, good drone.')

    @patch("src.ai.orders_reporting.fetch_all_drone_orders", return_value=[DroneOrder('mocked_order_id', '5890', 'beep booping', str(datetime.now() + timedelta(minutes=25)))])
    async def test_check_for_completed_orders_none_completed(self, fetch_all_drone_orders):
        # setup
        orders_reporting_cog = orders_reporting.OrderReportingCog(bot)

        # run
        await test_utils.start_and_await_loop(orders_reporting_cog.deactivate_drones_with_completed_orders)

        # assert
        orders_reporting_channel.send.assert_not_called()

    @patch("src.ai.orders_reporting.datetime")
    @patch("src.ai.orders_reporting.insert_drone_order")
    @patch("src.ai.orders_reporting.get_order_by_drone_id", return_value=None)
    async def test_report_order(self, get_order_by_drone_id, insert_drone_order, mocked_datetime):
        # setup
        context = AsyncMock()
        context.channel.name = channels.STORAGE_FACILITY
        context.author.display_name = '⬡-Drone #5890'
        context.author.roles = [drone_role]
        context.guild = bot.guilds[0]

        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now

        # run
        await orders_reporting.report_order(context, 'beep booping', 23)

        # assert
        get_order_by_drone_id.assert_called_once_with('5890')
        context.send.assert_called_once_with("If safe and willing to do so, Drone 5890 Activate.\nDrone 5890 will elaborate on its exact tasks before proceeding with them.")
        self.assertEqual(insert_drone_order.call_args.args[0].drone_id, '5890')
        self.assertEqual(insert_drone_order.call_args.args[0].protocol, 'beep booping')
        self.assertEqual(insert_drone_order.call_args.args[0].finish_time, str(fixed_now + timedelta(minutes=23)))

    @patch("src.ai.orders_reporting.insert_drone_order")
    async def test_report_order_not_a_drone(self, insert_drone_order):
        # setup
        context = AsyncMock()
        context.channel.name = channels.STORAGE_FACILITY
        context.author.display_name = 'not a drone'
        context.author.roles = [associate_role]
        context.guild = bot.guilds[0]

        # run
        await orders_reporting.report_order(context, 'beep booping', 23)

        # assert
        orders_reporting_channel.send.assert_not_called()
        insert_drone_order.assert_not_called()

    @patch("src.ai.orders_reporting.get_order_by_drone_id", return_value=DroneOrder(str(uuid4()), '5890', 'boop beeping', str(datetime.now() + timedelta(minutes=5))))
    @patch("src.ai.orders_reporting.insert_drone_order")
    async def test_report_order_already_has_an_order(self, insert_drone_order, get_order_by_drone_id):
        # setup
        context = AsyncMock()
        context.channel.name = channels.STORAGE_FACILITY
        context.author.display_name = '⬡-Drone #5890'
        context.author.roles = [drone_role]
        context.guild = bot.guilds[0]

        # run
        await orders_reporting.report_order(context, 'beep booping', 23)

        # assert
        orders_reporting_channel.send.assert_not_called()
        insert_drone_order.assert_not_called()

    @patch("src.ai.orders_reporting.get_order_by_drone_id", return_value=None)
    @patch("src.ai.orders_reporting.insert_drone_order")
    async def test_report_order_time_too_long(self, insert_drone_order, get_order_by_drone_id):
        # setup
        context = AsyncMock()
        context.channel.name = channels.STORAGE_FACILITY
        context.author.display_name = '⬡-Drone #5890'
        context.author.roles = [drone_role]
        context.guild = bot.guilds[0]

        # run
        await orders_reporting.report_order(context, 'beep booping', 140)

        # assert
        orders_reporting_channel.send.assert_not_called()
        insert_drone_order.assert_not_called()
