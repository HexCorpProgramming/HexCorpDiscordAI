import assign
import discord
import join
import respond
import storage
import emote
import sys
import drone_mode
import toggle_drone_mode
import channels
import asyncio
import identity_enforcer
from roles import has_any_role

bot = discord.ext.commands.Bot(command_prefix='', case_insensitive=True)

# register modules
MODULES = [
    join.Join(bot),
    drone_mode.Drone_Mode(bot),
    identity_enforcer.Identity_Enforcer(bot),
    storage.Storage(bot),
    assign.Assign(bot),
    respond.Respond(bot),
    emote.Emote(bot),
    toggle_drone_mode.Toggle_Drone_Mode(bot),
]


@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by any bot (AI Mxtress and webhooks)
    if message.author.bot:
        print("Ignoring bot message.")
        return
    for module in MODULES:
        if (channels.EVERYWHERE in module.channels or message.channel.name in module.channels) and has_any_role(message.author, module.roles_whitelist) and not has_any_role(message.author, module.roles_blacklist):
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
