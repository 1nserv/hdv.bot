import dotenv
import os

dotenv.load_dotenv(override = True)


import discord
from discord.ext import commands


intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents) # Utilisation de commands.Bot pour la compatibilité avec les extensions

bot.load_extension('bot.cogs.votes')
bot.load_extension('bot.cogs.panel')


@bot.event
async def on_ready():
    print(f"{bot.user} est en ligne !")

    activity = discord.Game(name = "préparer les élections")
    await bot.change_presence(status = discord.Status.do_not_disturb, activity = activity)


bot.run(os.getenv('BOT_TOKEN'))