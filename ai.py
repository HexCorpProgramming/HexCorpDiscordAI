#Core
import discord
import sys
import asyncio
#Modules
from identity_enforcer import Identity_Enforcer
from speech_optimization import Speech_Optimization
from toggle_speech_optimization import Toggle_Speech_Optimization
from join import Join
from respond import Respond
from storage import Storage
from emote import Emote
from assign import Assign
#Constants
from roles import has_any_role
import channels

bot = discord.ext.commands.Bot(command_prefix='', case_insensitive=True)

# register modules
MODULES = [
    Join(bot),
    Speech_Optimization(bot),
    Identity_Enforcer(bot),
    Storage(bot),
    Assign(bot),
    Respond(bot),
    Emote(bot),
    Toggle_Speech_Optimization(bot)
]


@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        print("Ignoring bot message.")
        return

    for module in MODULES:
        channel_valid = message.channel.name not in module.channels_blacklist and (message.channel.name in module.channels_whitelist or channels.EVERYWHERE in module.channels_whitelist)
        roles_valid = has_any_role(message.author, module.roles_whitelist) and not has_any_role(message.author, module.roles_blacklist)
        if channel_valid and roles_valid:
            for listener in module.on_message:
                # when a listener returns True, event has been handled
                print("Executing listener: " + str(listener) + " for message: [" + message.content + "] in server " + message.guild.name)
                if await listener(message):
                    print("Listener returned true. Terminating early.")
                    return
    print("Module stack execution complete.")


@bot.event
async def on_member_join(member: discord.Member):
    for module in MODULES:
        try:
            await module.on_member_join(member)
        except AttributeError:
            # do not raise an error, if this is not defined
            pass

@bot.event
async def on_ready():
    for module in MODULES:
        for listener in module.on_ready:
            # start these concurrently, so they do not block each other
            asyncio.ensure_future(listener())

bot.run(sys.argv[1])
