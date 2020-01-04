import discord
import join

bot = discord.ext.commands.Bot('')

# register Cogs
bot.add_cog(join.Join())

bot.run('token here')
