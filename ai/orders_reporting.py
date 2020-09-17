import asyncio
import logging
from uuid import uuid4
from datetime import datetime, timedelta
from discord.utils import get
from channels import ORDERS_REPORTING
from bot_utils import get_id
from db.drone_order_dao import delete_drone_order, insert_drone_order, fetch_all_drone_orders, get_order_by_drone_id
from db.data_objects import DroneOrder
from id_converter import convert_id_to_member
from roles import DRONE, has_role

LOGGER = logging.getLogger('ai')


async def start_check_for_completed_orders(bot):
    orders_reporting_channel = get(bot.guilds[0].channels, name=ORDERS_REPORTING)
    LOGGER.info("Beginning routine check for completed orders.")
    while True:
        # Check active orders every minute.
        await asyncio.sleep(60)
        LOGGER.debug("Checking for completed orders")
        await check_for_completed_orders(bot, orders_reporting_channel)


async def check_for_completed_orders(bot, orders_reporting_channel):
    for order in fetch_all_drone_orders():
        LOGGER.info(f"Checking order of drone {order.drone_id} with protocol {order.protocol}")
        if datetime.now() > datetime.fromisoformat(order.finish_time):
            # find drone to deactivate
            member_to_deactivate = convert_id_to_member(bot.guilds[0], order.drone_id)
            await orders_reporting_channel.send(f"{member_to_deactivate.mention} Drone {order.drone_id} Deactivate.\nDrone {order.drone_id}, good drone.")
            delete_drone_order(order.id)


async def report_order(context, protocol_name, protocol_time: int):
    LOGGER.info("Order reported.")
    drone_id = get_id(context.author.display_name)
    if not has_role(context.author, DRONE):
        return  # No non-drones allowed.
    current_order = get_order_by_drone_id(drone_id)

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
    insert_drone_order(created_order)
    LOGGER.info("Active order inserted and committed to DB.")
