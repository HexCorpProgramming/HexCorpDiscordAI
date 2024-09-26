import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import test.test_utils as test_utils
from test.cog import cog
from test.mocks import Mocks
from src.ai.orders_reporting import OrderReportingCog
from src.channels import ORDERS_REPORTING


class OrdersReportingTest(unittest.IsolatedAsyncioTestCase):

    mocks: Mocks
    channel: MagicMock

    @cog(OrderReportingCog)
    async def asyncSetUp(self, mocks: Mocks) -> None:
        self.mocks = mocks
        self.channel = self.mocks.channel(ORDERS_REPORTING)

    @patch("src.ai.orders_reporting.DroneOrder")
    async def test_check_for_completed_orders_completed(self, DroneOrders: MagicMock) -> None:

        activated_member = self.mocks.drone_member('1234', drone_order=self.mocks.drone_order())
        DroneOrders.all_drones = AsyncMock(return_value=[activated_member])

        await test_utils.start_and_await_loop(self.mocks.get_cog().deactivate_drones_with_completed_orders)

        self.mocks.channel(ORDERS_REPORTING).send.assert_called_once_with(activated_member.mention + ' Drone 1234 Deactivate.\nDrone 1234, good drone.')

    @patch("src.ai.orders_reporting.DroneOrder")
    async def test_check_for_completed_orders_none_completed(self, DroneOrders: MagicMock) -> None:
        activated_member = self.mocks.drone_member('1234', drone_order=self.mocks.drone_order(finish_time=datetime.now() + timedelta(minutes=25)))
        DroneOrders.all_drones = AsyncMock(return_value=[activated_member])

        await test_utils.start_and_await_loop(self.mocks.get_cog().deactivate_drones_with_completed_orders)

        self.mocks.channel(ORDERS_REPORTING).send.assert_not_called()

    @patch("src.ai.orders_reporting.DroneOrder")
    @patch("src.ai.orders_reporting.datetime")
    @patch("src.ai.orders_reporting.DroneMember")
    async def test_report_order(self, DroneMember: MagicMock, mocked_datetime: MagicMock, DroneOrder: MagicMock) -> None:
        # setup
        author = self.mocks.drone_member('1234')
        message = self.mocks.command(author, ORDERS_REPORTING, 'report "beeping booping" 23')
        fixed_now = datetime.now()
        mocked_datetime.now.return_value = fixed_now
        order = self.mocks.drone_order()

        def create_order(id: str, discord_id: int, protocol: str, finish_time: str) -> MagicMock:
            order.id = id
            order.discord_id = discord_id
            order.protocol = protocol
            order.finish_time = finish_time
            return order

        DroneOrder.side_effect = create_order

        DroneMember.load = AsyncMock(return_value=author)

        # run
        await self.assert_command_successful(message)

        # assert
        self.mocks.get_bot().context.send.assert_called_once_with("If safe and willing to do so, Drone 1234 Activate.\nDrone 1234 will elaborate on its exact tasks before proceeding with them.")
        self.assertEqual(order.discord_id, author.id)
        self.assertEqual(order.protocol, 'beeping booping')
        self.assertEqual(order.finish_time, str(fixed_now + timedelta(minutes=23)))
        order.insert.assert_called_once()

    @patch("src.ai.orders_reporting.DroneMember")
    async def test_report_order_not_a_drone(self, DroneMember: MagicMock) -> None:
        # setup
        author = self.mocks.drone_member('1234', drone=None)
        message = self.mocks.command(author, ORDERS_REPORTING, 'report "beeping booping" 23')
        DroneMember.load = AsyncMock(return_value=author)

        # run
        await self.assert_command_error(message, 'This command is only available to drones.')

    @patch("src.ai.orders_reporting.DroneMember")
    async def test_report_order_already_has_an_order(self, DroneMember: MagicMock) -> None:
        # setup
        author = self.mocks.drone_member('1234')
        author.drone.order = self.mocks.drone_order()
        message = self.mocks.command(author, ORDERS_REPORTING, 'report "beeping booping" 23')
        DroneMember.load = AsyncMock(return_value=author)

        # run
        await self.assert_command_error(message, 'HexDrone #1234 is already undertaking the  protocol.')

    @patch("src.ai.orders_reporting.DroneMember")
    async def test_report_order_time_too_long(self, DroneMember: MagicMock) -> None:
        # setup
        author = self.mocks.drone_member('1234')
        message = self.mocks.command(author, ORDERS_REPORTING, 'report "beeping booping" 140')
        DroneMember.load = AsyncMock(return_value=author)

        # run
        await self.assert_command_error(message, 'Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.')
