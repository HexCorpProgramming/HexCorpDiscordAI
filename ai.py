import assign
import discord
import join
import respond
import storage
import emote
import sys

bot = discord.ext.commands.Bot("h! ")

# register Cogs
bot.add_cog(join.Join(bot))
bot.add_cog(assign.Assign(bot))
bot.add_cog(respond.Respond(bot))
bot.add_cog(emote.Emote(bot))
# bot.add_cog(storage.Storage(bot))

print("Hello, world!")

#bot.run(sys.argv[1])
bot.run("NjczNDcwMTA0NTE5ODM1NjU5.Xnz_mg.527BdWZXLWUpTY3qq9140hKanhg")
