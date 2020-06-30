import discord
import logging
from discord.utils import get
from channels import REPETITIONS
from roles import HIVE_MXTRESS

class Mantras():

    current_mantra = ""

    async def load_mantra(self):
        if Mantras.current_mantra != "": return True #No need to load a mantra if it's already there.
        with open("current_mantra", "r") as mantra_file:
            Mantras.current_mantra = mantra_file.readline()
            self.LOGGER.info(f"Mantra loaded from file: {Mantras.current_mantra}")
            mantra_file.close()

    async def update_mantra(self, message):

        print("CURRENT MANTRA IS:")
        print(Mantras.current_mantra)

        if message.content.startswith("Repeat :: ") == False: return False #Only accept for the correct format.
        new_mantra = message.content.replace("Repeat :: ","")
        with open("current_mantra", "w") as mantra_file:
            mantra_file.write(new_mantra)
            Mantras.current_mantra = new_mantra #Update the global mantra.
            topic_message = message.content.replace("Repeat :: ", "Repeat :: [ID] :: ")
            await message.channel.edit(topic=topic_message) #Update the channel description
            self.LOGGER.info(f"Mantra updated and written to file: {Mantras.current_mantra}")
            mantra_file.close()

        print("UPDATED MANTRA IS:")
        print(Mantras.current_mantra)

        return True

    def __init__(self, bot):
        self.bot = bot
        self.channels_whitelist = [REPETITIONS]
        self.channels_blacklist = []
        self.roles_whitelist = [HIVE_MXTRESS]
        self.roles_blacklist = []
        self.on_message = [self.update_mantra]
        self.on_ready = [self.load_mantra]
        self.LOGGER = logging.getLogger('ai')