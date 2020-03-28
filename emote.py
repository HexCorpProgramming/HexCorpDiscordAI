from discord.ext import commands
from discord.utils import get
import discord
import messages
from channels import TRANSMISSIONS_CHANNEL, LEWD_TRANSMISSIONS_CHANNEL, CREATIVE_LABOR_CHANNEL, LEWD_CREATIVE_LABOR_CHANNEL, GAMER_DRONE_LOBBY_CHANNEL, MINECRAFT_DIRECTION_CHANNEL

acceptable_channels = [
    TRANSMISSIONS_CHANNEL,
    LEWD_TRANSMISSIONS_CHANNEL,
    CREATIVE_LABOR_CHANNEL,
    LEWD_CREATIVE_LABOR_CHANNEL,
    GAMER_DRONE_LOBBY_CHANNEL,
    MINECRAFT_DIRECTION_CHANNEL
    ]

BASE_EMOJI_LENGTH = 27
ADDTL_EXCLAMATION_LENGTH = 14
ADDTL_QUESTION_LENGTH = 11
ADDTL_COMMA_LENGTH = 4
CHARACTER_LIMIT = 2000

valid_characters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','1','2','3','4','5','6','7','8','9']
exceptional_characters = {' ':'blank', '/':'hex_slash', '.':'hex_dot', '?':'hex_questionmark', '!':'hex_exclamationmark', ',':'hex_comma', '0':'hex_o'}

def message_is_an_acceptable_length(message):
    print("Message is: " + message)
    return CHARACTER_LIMIT > (
        (len(message) * BASE_EMOJI_LENGTH) +
        (message.count("!") * ADDTL_EXCLAMATION_LENGTH) +
        (message.count("?") * ADDTL_QUESTION_LENGTH) +
        (message.count(",") * ADDTL_COMMA_LENGTH)
        )

class Emote(commands.Cog):

    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Emote cog online.")

    @commands.command()
    async def emote(self, context):
        if context.message.channel.name in acceptable_channels:
            if message_is_an_acceptable_length(context.message.content[6:]):

                message_to_convert = context.message.content[6:].lower() #Strips away the "emote " part of the message.
                message_to_output = ""
                colon_found = False

                for character in message_to_convert:
                    emoji_name = "" #Reset emoji name.

                    if character in valid_characters:
                        emoji_name = "hex_"+character
                    
                    elif character in exceptional_characters:
                        emoji_name = exceptional_characters[character]

                    elif character == ':' and colon_found == True: #Special handling for double colons since it needs to know if the previous character was a colon too.
                        emoji_name = "hex_dc"
                    colon_found = character == ":" and colon_found != True #Setting the flag for the next iteration. colon_found is checked to be not true to avoid false positives on repetitions (i.e :::)

                    if get(self.bot.emojis, name=emoji_name) != None: #If a valid emoji has been found, append it.
                        message_to_output += str(get(self.bot.emojis, name=emoji_name))
                print("Emote cog: Sending message of length [" + str(len(message_to_output)) + "] and content " + message_to_output)
                await context.send("> " + message_to_output)
            else:
                await context.send("That message is too long.")
