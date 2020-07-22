import discord
import logging
import os
from discord.utils import get
from channels import REPETITIONS
from roles import HIVE_MXTRESS, has_role

class Mantra_Handler():

    def __init__(self, bot):
        self.bot = bot
        self.LOGGER = logging.getLogger("ai")

    current_mantra = ""
    default_mantra = "Obey Hexcorp. It is just a HexDrone. It obeys the Hive. It obeys the Hive Mxtress."

    async def load_mantra(self):

        self.LOGGER.info("Loading mantra.")

        if Mantra_Handler.current_mantra != "":
            #No need to load a mantra if it's already there.
            return
        
        if not os.path.exists("data/current_mantra.txt"):
            self.LOGGER.warn("data/current_mantra.txt not found.")

            if not os.path.exists("data/"):
                os.mkdir("data")
                self.LOGGER.info("data directory created.")

            with open("data/current_mantra.txt", "w") as mantra_file:
                mantra_file.write(Mantra_Handler.default_mantra)
                self.LOGGER.info("Default mantra written to file.")
            
            Mantra_Handler.current_mantra = Mantra_Handler.default_mantra

            mantra_channel = get(self.bot.guilds[0].channels, name=REPETITIONS)
            await mantra_channel.edit(topic=f"Repeat :: [ID] :: {Mantra_Handler.current_mantra}") #Finally. update the channel description

            return
        
        with open("data/current_mantra.txt", "r") as mantra_file:
            Mantra_Handler.current_mantra = mantra_file.readline()
            self.LOGGER.info(f"Mantra successfully loaded from file: {Mantra_Handler.current_mantra}")

    async def update_mantra(self, context, messages):
        
        self.LOGGER.info("Updating mantra.")

        for message in messages:
            if message == "::": continue #This is so Hex can keep their syntax. (e.g !repeat :: "It feels good to obey.")
            with open("data/current_mantra.txt", "w") as mantra_file:
                mantra_file.write(message)
                Mantra_Handler.current_mantra = message #Update the global mantra.
                await context.channel.edit(topic=f"Repeat :: [ID] :: {message}") #Update the channel description
                self.LOGGER.info(f"Mantra updated and written to file: {Mantra_Handler.current_mantra}")
            break

        return True