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
from db.drone_order import delete_drone_order, insert_drone_order, fetch_all_drone_orders

LOGGER = logging.getLogger('ai')


class ActiveOrder():
    def __init__(self, id: str, drone_id: str, protocol: str, finish_time: str):
        self.id = id
        self.drone_id = drone_id
        self.protocol = protocol
        self.finish_time = finish_time


class Orders_Reporting():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [ORDERS_REPORTING]
        self.channels_blacklist = []
        self.roles_whitelist = [DRONE]
        self.roles_blacklist = []
        self.on_message = [self.order_reported]
        self.on_ready = [self.report_online,
                         self.monitor_progress]
        self.monitor_progress_started = False
        self.message_format = r"Drone \d{4} is ready to be activated and obey orders\. Drone \d{4} will be obeying the :: \w.+ protocol for \d{1,3} (minutes|minute)\.?"

    async def report_online(self):
        LOGGER.info("Orders reporting module online.")

    async def monitor_progress(self):
        if self.monitor_progress_started:
            return

        self.monitor_progress_started = True
        ORDERS_REPORTING_CHANNEL = get(
            self.bot.guilds[0].channels, name=ORDERS_REPORTING)
        while True:
            # Check active orders every minute.
            await asyncio.sleep(60)
            LOGGER.debug("Checking for completed orders")
            for order in fetch_all_drone_orders():
                if datetime.now() > datetime.fromisoformat(order.finish_time):
                    for member in self.bot.guilds[0].members:
                        if get_id(member.display_name) == order.drone_id:
                            # get the drone responsible
                            await ORDERS_REPORTING_CHANNEL.send(f"{member.mention} Drone {order.drone_id} Deactivate.\nDrone {order.drone_id}, good drone.")
                            delete_drone_order(order.id)

    async def order_reported(self, message: discord.Message):
        LOGGER.debug("Possible order reported.")
        if re.fullmatch(self.message_format, message.content) is None:
            return

        LOGGER.debug("A valid order has been reported.")

        drone_id = re.search(r"\d{4}", message.content).group()

        drone_id_from_user = re.search(
            r"\d{4}", message.author.display_name).group()

        if drone_id != drone_id_from_user:
            await message.channel.send("Your drone ID does not match the declaration.")
            return

        for order in fetch_all_drone_orders():
            if order.user_id == message.author.id:
                await message.channel.send(f"Drone {drone_id} has already been assigned an order.")
                return

        protocol_name = re.search(r":: \w.+ protocol", message.content).group()
        protocol_name = protocol_name[3:]
        protocol_time = re.search(
            r"(?<!\d)\d{1,3}(?!\d)", message.content).group()

        if int(protocol_time) > 120:
            await message.channel.send("Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.")
            return

        await message.channel.send(f"Drone {drone_id} Activate.\nDrone {drone_id} will elaborate on its exact tasks before proceeding with them.")
        finish_time = str(
            datetime.now() + timedelta(minutes=int(protocol_time)))
        created_order = ActiveOrder(
            str(uuid4()), drone_id, protocol_name, finish_time)
        insert_drone_order(created_order)

        return False
