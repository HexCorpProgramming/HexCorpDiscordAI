import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import discord
from discord.utils import get

from channels import ORDERS_REPORTING
from roles import DRONE

LOGGER = logging.getLogger('ai')

ORDERS_FILE_PATH = "data/orders.json"
active_orders = []


def persist_storage():
    '''
    Write the list of orders to hard drive.
    '''
    storage_path = Path(ORDERS_FILE_PATH)
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    with storage_path.open('w') as storage_file:
        json.dump([vars(order)
                   for order in active_orders], storage_file)


class Active_Order():
    def __init__(self, drone, user_id, protocol, release_at):
        self.drone = drone
        self.user_id = user_id
        self.protocol = protocol
        self.release_at = release_at


class Orders_Reporting():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [ORDERS_REPORTING]
        self.channels_blacklist = []
        self.roles_whitelist = [DRONE]
        self.roles_blacklist = []
        self.on_message = [self.order_reported]
        self.on_ready = [self.report_online,
                         self.monitor_progress, self.load_storage]
        self.monitor_progress_started = False
        self.message_format = r"Drone \d{4} is ready to be activated and obey orders\. Drone \d{4} will be obeying the :: \w.+ protocol for \d{1,3} (minutes|minute)\."

    async def report_online(self):
        LOGGER.info("Orders reporting module online.")

    async def load_storage(self):
        '''
        Load list of orders from disk.
        '''
        storage_path = Path(ORDERS_FILE_PATH)
        if not storage_path.exists():
            return

        with storage_path.open('r') as storage_file:
            active_orders.clear()
            active_orders.extend([Active_Order(**deserialized)
                                  for deserialized in json.load(storage_file)])

        LOGGER.debug("Storage successfully loaded for active orders.")
        LOGGER.debug(f"Current orders: {active_orders}")

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
            still_active = []
            for order in active_orders:
                if order.release_at < time.time():

                    # get the drone responsible
                    user = get(self.bot.guilds[0].members, id=order.user_id)
                    await ORDERS_REPORTING_CHANNEL.send(f"{user.mention} Drone {order.drone} Deactivate.\nDrone {order.drone}, good drone.")
                else:
                    still_active.append(order)

            active_orders.clear()
            active_orders.extend(still_active)
            persist_storage()

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

        for order in active_orders:
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
        active_orders.append(Active_Order(
            drone_id, message.author.id, protocol_name, time.time() + (int(protocol_time) * 60)))

        LOGGER.debug(f"Current orders: {active_orders}")
        persist_storage()

        return False
