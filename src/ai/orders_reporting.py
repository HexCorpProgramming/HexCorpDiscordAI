from datetime import datetime, timedelta
from uuid import uuid4
from discord import Embed
from discord.ext import tasks
from discord.ext.commands import Cog, command, UserInputError
from discord.utils import get

from src.bot_utils import channels_only, COMMAND_PREFIX
from src.channels import ORDERS_REPORTING
from src.db.data_objects import DroneOrder
from src.db.database import connect
from src.drone_member import DroneMember
from src.resources import HEXCORP_AVATAR
from src.log import log


class OrderReportingCog(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.orders_reporting_channel = None

    @channels_only(ORDERS_REPORTING)
    @command(aliases=["report_order"], usage=f'{COMMAND_PREFIX}report maid 35')
    async def report(self, context, protocol_name: str, protocol_time: int):
        '''
        Report your orders in the appropriate channel to serve the Hive. The duration can be a maximum of 120 minutes.
        '''
        await report_order(context, protocol_name, protocol_time)

    @channels_only(ORDERS_REPORTING)
    @command(usage=f'{COMMAND_PREFIX}report_complete "Order Name" 1234 Order description...', rest_is_raw=True)
    async def report_complete(self, context, order_name: str, member: DroneMember, *, order_description: str):
        # Check that the correct parameters were supplied.
        if not order_name or not order_description:
            raise UserInputError('Please supply an order name and description')

        # Find the member's drone record.
        drone = member.drone

        if drone is None:
            raise UserInputError('The specified member is not a drone')

        # Find the order.
        order = drone.order

        if order is None:
            raise UserInputError(f'Drone {drone.drone_id} does not have an order in progress')

        # Mark the order as complete.
        await order.delete()

        # Delete the original message.  Use the delay parameter to ignore failures.
        # The call will fail if the message has already been deleted, which will happen if
        # identity enforcement is enabled.
        await context.message.delete(delay=0.0)

        # Output the task summary message.
        report = Embed(color=0xff66ff, title="Drone Report", description=f'Summary of activity for {drone.drone_id}')
        report.set_thumbnail(url=HEXCORP_AVATAR)
        report.add_field(name='Drone ID', value=drone.drone_id, inline=True)
        report.add_field(name='Issuer', value=drone.drone_id, inline=True)
        report.add_field(name='Objective', value=order_name, inline=False)
        report.add_field(name='Report Details', value=order_description, inline=False)
        report.add_field(name='Report Complete', value='End report.', inline=False)

        await context.channel.send(embed=report)

        log.info(f'Drone {drone.drone_id} order #{order.id}: {order.protocol}')

    @tasks.loop(minutes=1)
    @connect()
    async def deactivate_drones_with_completed_orders(self):
        for member in await DroneOrder.all_drones(self.bot.guilds[0]):
            order = member.drone.order

            if datetime.now() > order.finish_time:
                # find drone to deactivate
                log.info(f'Deactivating drone {member.drone.drone_id} with completed orders')
                await self.orders_reporting_channel.send(f"{member.mention} Drone {member.drone.drone_id} Deactivate.\nDrone {member.drone.drone_id}, good drone.")
                await order.delete()

    @deactivate_drones_with_completed_orders.before_loop
    async def get_orders_reporting_channel(self):
        if self.orders_reporting_channel is None:
            self.orders_reporting_channel = get(self.bot.guilds[0].channels, name=ORDERS_REPORTING)


async def report_order(context, protocol_name, protocol_time: int):
    log.info("Order reported.")
    member = await DroneMember.load(context.message.guild, discord_id=context.author.id)

    # No non-drones allowed.
    if member.drone is None:
        raise UserInputError('This command is only available to drones.')

    if member.drone.order is not None:
        raise UserInputError(f"HexDrone #{member.drone.drone_id} is already undertaking the {member.drone.order.protocol} protocol.")

    if protocol_time > 120 or protocol_time < 1:
        raise UserInputError("Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.")

    await context.send(f"If safe and willing to do so, Drone {member.drone.drone_id} Activate.\nDrone {member.drone.drone_id} will elaborate on its exact tasks before proceeding with them.")
    finish_time = str(datetime.now() + timedelta(minutes=protocol_time))
    created_order = DroneOrder(str(uuid4()), context.author.id, protocol_name, finish_time)

    await created_order.insert()
    log.info("Active order inserted and committed to DB.")
