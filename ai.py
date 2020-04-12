import assign
import discord
import join
import respond
import storage
import emote
import sys
import drone_mode
import roles

bot = discord.ext.commands.Bot(command_prefix = '', case_insensitive = True)

# register modules
MODULES = [
    join.Join(bot)
]

# register Cogs
# bot.add_cog(assign.Assign(bot))
# bot.add_cog(respond.Respond(bot))
# bot.add_cog(emote.Emote(bot))
# bot.add_cog(drone_mode.Drone_Mode(bot))
# bot.add_cog(storage.Storage(bot))

@bot.event
async def on_message(message: discord.Message):
    # ignore all messages by the bot
    if message.author == bot.user:
            return

    for module in MODULES:
        if message.channel.name in module.channels and roles.has_any_role(message.author, module.roles):
            for listener in module.on_message:
                # when a listener returns True, event has been handled
                if await listener(message):
                    return

    await bot.process_commands(message)

@bot.event
async def on_member_join(member: discord.Member):
    for module in MODULES:
        if module.on_member_join is not None:
            await module.on_member_join(member)

bot.run(sys.argv[1])
