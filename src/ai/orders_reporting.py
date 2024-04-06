import logging
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Union
from src.validation_error import ValidationError

from discord import Member
from discord.ext import tasks
from discord.ext.commands import Cog, command, guild_only
from discord.utils import get

from src.bot_utils import COMMAND_PREFIX, get_id
from src.channels import ORDERS_REPORTING
from src.db.data_objects import DroneOrder
from src.db.database import connect
from src.db.drone_order_dao import (delete_drone_order, fetch_all_drone_orders,
                                    get_order_by_drone_id, insert_drone_order)
from src.db.drone_dao import fetch_drone_with_id
from src.roles import DRONE, has_role
from src.ai.commands import DroneMemberConverter

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

    @command(usage=f'{COMMAND_PREFIX}report_complete "Order Name" 1234 Order description...', rest_is_raw=True)
    async def report_complete(self, context, order_name: str, member: Union[Member | DroneMemberConverter], *, order_description: str):
        # Check that the command was issued in the correct channel.
        if context.channel.name != ORDERS_REPORTING:
            raise ValidationError(f'This command may only be used in #{ORDERS_REPORTING}')

        # Check that the correct parameters were supplied.
        if not order_name or not order_description:
            raise ValidationError('Please supply an order name and description')

        # Find the member's drone record.
        drone = await fetch_drone_with_id(member.id)

        if drone is None:
            raise ValidationError('The specified member is not a drone')

        # Find the order.
        order = await get_order_by_drone_id(drone.drone_id)

        if order is None:
            raise ValidationError(f'Drone {drone.drone_id} does not have an order in progress')

        # Mark the order as complete.
        await delete_drone_order(order.id)

        # Delete the original message.
        await context.message.delete()

        # Output the task summary message.
        report = ('===Drone Report===\n'
                  f'Drone ID: {order.drone_id}\n'
                  f'Objective: {order_name}\n'
                  f'Issuer: {drone.drone_id}\n'
                  '\n'
                  'Report Details:\n'
                  f'{order_description}\n'
                  '\n'
                  'End report.')

        await context.channel.send(report)

        LOGGER.info(f'Drone {drone.drone_id} order #{order.id}: {order.protocol}')

    @tasks.loop(minutes=1)
    @connect()
    async def deactivate_drones_with_completed_orders(self):
        for order in await fetch_all_drone_orders():
            if datetime.now() > datetime.fromisoformat(order.finish_time):
                # find drone to deactivate
                member_to_deactivate = self.bot.guilds[0].get_member(order.discord_id)
                drone = await fetch_drone_with_id(order.discord_id)
                LOGGER.info(f'Deactivating drone {drone.drone_id} with completed orders')
                await self.orders_reporting_channel.send(f"{member_to_deactivate.mention} Drone {drone.drone_id} Deactivate.\nDrone {drone.drone_id}, good drone.")
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
        str(uuid4()), context.author.id, protocol_name, finish_time)
    LOGGER.info("ActiveOrder object created. Inserting order.")
    await insert_drone_order(created_order)
    LOGGER.info("Active order inserted and committed to DB.")
