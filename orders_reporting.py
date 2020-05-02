import discord
import re
from channels import ORDERS_REPORTING
from roles import DRONE

ORDERS_FILE_PATH = "data/orders.json"
ACTIVE_ORDERS = []

class Orders_Reporting():

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [ORDERS_REPORTING]
        self.channels_blacklist = []
        self.roles_whitelist = [DRONE]
        self.roles_blacklist = []
        self.on_message = [self.order_reported]
        self.on_ready = [self.report_online]
        self.message_format = r"Drone \d{4} is ready to be activated and obey orders\. Drone \d{4} will be obeying the :: \w.+ protocol for \d{1,3} minutes\."

    async def report_online(self):
        print("Orders reporting module online.")

    async def order_reported(self, message: discord.Message):
        print("An order has been reported, maybe.")
        if re.fullmatch(self.message_format, message.content) is None:
            print("Message in orders reporting does not match the regex.")
            return

        print("A valid message has been found.")
        drone_id = re.search(r"\d{4}", message.content).group()
        protocol_name = re.search(r":: \w.+ protocol", message.content).group()
        protocol_name = protocol_name[3:]
        protocol_time = re.search(r"(?<!\d)\d{1,3}(?!\d)", message.content).group()

        if int(protocol_time) > 120:
            await message.channel.send("Drones are not authorized to activate a specific protocol for that length of time. The maximum is 120 minutes.")
            return

        await message.channel.send(f"Drone {drone_id} activate.")
        await message.channel.send(f"Drone {drone_id} will elaborate on its exact tasks before proceeding with them.")

        return False

    def persist_storage():
    '''
    Write the list of stored drones to hard drive.
    '''
    storage_path = Path(STORAGE_FILE_PATH)
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    with storage_path.open('w') as storage_file:
        json.dump([vars(stored_drone)
                   for stored_drone in STORED_DRONES], storage_file)

    async def load_storage(self):
        '''
        Load storage list from disk.
        '''
        storage_path = Path(STORAGE_FILE_PATH)
        if not storage_path.exists():
            return

        with storage_path.open('r') as storage_file:
            ACTIVE_ORDERS.clear()
            ACTIVE_ORDERS.extend([StoredDrone(**deserialized)
                                  for deserialized in json.load(storage_file)])


        


    


