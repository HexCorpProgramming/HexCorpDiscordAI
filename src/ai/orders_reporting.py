import logging
from datetime import datetime, timedelta
from uuid import uuid4

from discord.ext import tasks
from discord.ext.commands import Cog, guild_only
from discord.utils import get

from src.bot_utils import command, COMMAND_PREFIX, get_id
from src.channels import ORDERS_REPORTING
from src.db.data_objects import DroneOrder
from src.db.database import connect
from src.db.drone_order_dao import (delete_drone_order, fetch_all_drone_orders,
                                    get_order_by_drone_id, insert_drone_order)
from src.id_converter import convert_id_to_member
from src.roles import DRONE, has_role

LOGGER = logging.getLogger('ai')


class OrderReportingCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.orders_reporting_channel = None

    @guild_only()
    @command(aliases=["report_order"], usage=f'{COMMAND_PREFIX}report maid 35')
    async def report(self, context, protocol_name: str, protocol_time: int):
        '''
        Report your orders in the appropriate channel to serve the Hive. The duration can be a maximum of 120 minutes.
        '''
        try:
            int(protocol_time)
        except ValueError:
            await context.send("Your protocol time must be an integer (whole number) between 1 and 120 minutes.")

        if context.channel.name == ORDERS_REPORTING:
            await report_order(context, protocol_name, protocol_time)

    @tasks.loop(minutes=1)
    @connect()
    async def deactivate_drones_with_completed_orders(self):
        for order in await fetch_all_drone_orders():
            LOGGER.info(f"Checking order of drone {order.drone_id} with protocol {order.protocol}")
            if datetime.now() > datetime.fromisoformat(order.finish_time):
                # find drone to deactivate
                member_to_deactivate = await convert_id_to_member(self.bot.guilds[0], order.drone_id)
                await self.orders_reporting_channel.send(f"{member_to_deactivate.mention} Drone {order.drone_id} Deactivate.\nDrone {order.drone_id}, good drone.")
                await delete_drone_order(order.id)

    @deactivate_drones_with_completed_orders.before_loop
    async def get_orders_reporting_channel(self):
        if self.orders_reporting_channel is None:
            self.orders_reporting_channel = get(self.bot.guilds[0].channels, name=ORDERS_REPORTING)


async def report_order(context, protocol_name, protocol_time: int):
    LOGGER.info("Order reported.")
    drone_id = get_id(context.author.display_name)
    if not has_role(context.author, DRONE):
        return  # No non-drones allowed.
    current_order = await get_order_by_drone_id(drone_id)

    if current_order is not None:
        await context.send(f"HexDrone #{drone_id} is already undertaking the {current_order.protocol} protocol.")
        return

    if protocol_time > 120 or protocol_time < 1:
        await context.send("Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.")
        return

    await context.send(f"If safe and willing to do so, Drone {drone_id} Activate.\nDrone {drone_id} will elaborate on its exact tasks before proceeding with them.")
    finish_time = str(
        datetime.now() + timedelta(minutes=protocol_time))
    created_order = DroneOrder(
        str(uuid4()), drone_id, protocol_name, finish_time)
    LOGGER.info("ActiveOrder object created. Inserting order.")
    await insert_drone_order(created_order)
    LOGGER.info("Active order inserted and committed to DB.")
