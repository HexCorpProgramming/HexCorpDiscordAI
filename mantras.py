import discord
import logging
import os
from discord.utils import get
from channels import REPETITIONS
from roles import HIVE_MXTRESS

class Mantras():

    current_mantra = ""
    default_mantra = "Obey Hexcorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress."

    async def load_mantra(self):

        self.LOGGER.info("Loading mantra.")

        if Mantras.current_mantra != "":
            #No need to load a mantra if it's already there.
            return
        
        if not os.path.exists("data/current_mantra.txt"):
            self.LOGGER.warn("data/current_mantra.txt not found.")

            if not os.path.exists("data/"):
                os.mkdir("data")
                self.LOGGER.info("data directory created.")

            with open("data/current_mantra.txt", "w") as mantra_file:
                mantra_file.write(Mantras.default_mantra)
                self.LOGGER.info("Default mantra written to file.")
            
            Mantras.current_mantra = Mantras.default_mantra

            mantra_channel = get(self.bot.guilds[0].channels, name=REPETITIONS)
            await mantra_channel.edit(topic=f"Repeat :: [ID] :: {Mantras.current_mantra}") #Finally. update the channel description

            return
        
        with open("data/current_mantra.txt", "r") as mantra_file:
            Mantras.current_mantra = mantra_file.readline()
            self.LOGGER.info(f"Mantra successfully loaded from file: {Mantras.current_mantra}")

    async def update_mantra(self, message):

        if message.content.startswith("Repeat :: ") == False: return False
        new_mantra = message.content.replace("Repeat :: ","")
        with open("data/current_mantra.txt", "w") as mantra_file:
            mantra_file.write(new_mantra)
            Mantras.current_mantra = new_mantra #Update the global mantra.
            topic_message = message.content.replace("Repeat :: ", "Repeat :: [ID] :: ")
            await message.channel.edit(topic=topic_message) #Update the channel description
            self.LOGGER.info(f"Mantra updated and written to file: {Mantras.current_mantra}")

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
