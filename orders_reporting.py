import discord
from channels import ORDERS_REPORTING
from roles import DRONE

class Orders_Reporting():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [ORDERS_REPORTING]
        self.channels_blacklist = []
        self.roles_whitelist = [DRONE]
        self.roles_blacklist = []
        self.on_message = [self.order_reported]
        self.on_ready = [self.report_online]

    def report_online(self):
        print("Orders reporting module online.")

    def order_reported(self):
        print("An order has been reported, maybe.")
