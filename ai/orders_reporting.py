import asyncio
import logging
from uuid import uuid4
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import discord
from discord.utils import get

from channels import ORDERS_REPORTING
from roles import DRONE
from bot_utils import get_id
from db.drone_order_dao import delete_drone_order, insert_drone_order, fetch_all_drone_orders, get_order_by_drone_id

LOGGER = logging.getLogger('ai')

class ActiveOrder():
    def __init__(self, id: str, drone_id: str, protocol: str, finish_time: str):
        self.id = id
        self.drone_id = drone_id
        self.protocol = protocol
        self.finish_time = finish_time

async def check_for_completed_orders(bot):
    ORDERS_REPORTING_CHANNEL = get(bot.guilds[0].channels, name=ORDERS_REPORTING)
    LOGGER.info("Beginning routine check for completed orders.")
    while True:
        # Check active orders every minute.
        await asyncio.sleep(10)
        LOGGER.debug("Checking for completed orders")
        for order in fetch_all_drone_orders():
            LOGGER.info(f"Checking order of drone {order.drone_id} with protocol {order.protocol}")
            if datetime.now() > datetime.fromisoformat(order.finish_time):
                for member in bot.guilds[0].members:
                    if get_id(member.display_name) == order.drone_id:
                        # get the drone responsible
                        await ORDERS_REPORTING_CHANNEL.send(f"{member.mention} Drone {order.drone_id} Deactivate.\nDrone {order.drone_id}, good drone.")
                        delete_drone_order(order.id)

async def report_order(context, protocol_name, protocol_time):
    LOGGER.info("Order reported.")
    drone_id = get_id(context.author.display_name)
    if drone_id is None: return #No non-drones allowed.
    current_order = get_order_by_drone_id(drone_id)

    if current_order is not None:
        await context.send(f"HexDrone #{drone_id} is already undertaking the {current_order.protocol} protocol.")
        return

    if int(protocol_time) > 120:
        await context.channel.send("Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.")
        return

    await context.send(f"Drone {drone_id} Activate.\nDrone {drone_id} will elaborate on its exact tasks before proceeding with them.")
    finish_time = str(
        datetime.now() + timedelta(minutes=int(protocol_time)))
    created_order = ActiveOrder(
        str(uuid4()), drone_id, protocol_name, finish_time)
    LOGGER.info("ActiveOrder object created. Inserting order.")
    insert_drone_order(created_order)
    LOGGER.info("Active order inserted and committed to DB.")
