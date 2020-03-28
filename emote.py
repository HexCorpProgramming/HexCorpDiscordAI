from discord.ext import commands
from discord.utils import get
import discord
import messages
from channels import TRANSMISSIONS_CHANNEL, LEWD_TRANSMISSIONS_CHANNEL, CREATIVE_LABOR_CHANNEL, LEWD_CREATIVE_LABOR_CHANNEL

acceptable_channels = [
    TRANSMISSIONS_CHANNEL,
    LEWD_TRANSMISSIONS_CHANNEL,
    CREATIVE_LABOR_CHANNEL,
    LEWD_CREATIVE_LABOR_CHANNEL
    ]

BASE_EMOJI_LENGTH = 27
ADDTL_EXCLAMATION_LENGTH = 14
ADDTL_QUESTION_LENGTH = 11
ADDTL_COMMA_LENGTH = 4
CHARACTER_LIMIT = 2000

message_to_convert = "Beep!"
message_to_output = ""

valid_characters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','1','2','3','4','5','6','7','8','9']

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
                    emoji_name = ""
                    if character == ' ':
                        emoji_name = "blank"
                    elif character == '/':
                        emoji_name = "hex_slash"
                    elif character == '.':
                        emoji_name = "hex_dot"
                    elif character == '?':
                        emoji_name = "hex_questionmark"
                    elif character == '!':
                        emoji_name = "hex_exclamationmark"
                    elif character == ',':
                        emoji_name = "hex_comma"
                    elif character == '0':
                        emoji_name = "hex_o"
                    elif character == ':':
                        emoji_name = "hex_dc" if colon_found else ""
                    else:
                        if character in valid_characters:
                            emoji_name = "hex_"+character
                    colon_found = character == ":"
                    if (str(get(self.bot.emojis, name=emoji_name))) != "None":
                        message_to_output += str(get(self.bot.emojis, name=emoji_name))
                print("Emote cog: Sending message of length [" + str(len(message_to_output)) + "] and content " + message_to_output)
                await context.send(message_to_output)
            else:
                print("Emote cog: Message of length [" + str(len(context.message.content[6:])) + "] not sent. (Too long).")
                await context.send("That message is too long.")
