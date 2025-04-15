import dotenv
import nsarchive
import os
from bot.utils import entities

from nsarchive import *

import discord
from discord.ext import commands
from discord.ui import View
from discord import Game
import bot.modals as modals

import bot.embeds as embeds
from functions import bot_functions

dotenv.load_dotenv(override = True)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)  # Utilisation de commands.Bot pour la compatibilité avec les extensions

#EVENT
@bot.event
async def on_ready():
    print(f"{bot.user} est en ligne !")
            
    activity = Game(name = "préparer les élections")
    await bot.change_presence(status = discord.Status.do_not_disturb, activity = activity)
    
@bot.slash_command(name="create_party", description="Créer son parti")
async def create_party(ctx: discord.ApplicationContext):
    user_id = nsarchive.NSID(ctx.author.id)
    entity = entities.get_entity(user_id)
        
    if bot_functions.is_citoyen(entity) != True and bot_functions.is_admin(ctx) != True:
        return await ctx.respond(embed=embeds.Bot.not_citoyen(), ephemeral=True)
        
    # vérifier son appartenance
    try:
        entity_groups = entity.groups()
        for org in entity_groups:
            if str(org.position).upper() == "PARTI":
                return await ctx.respond(embed=embeds.Parties.already_in_party(), ephemeral=True)
    except:
        pass
        
    modal = modals.CreatePartyModal()
    await ctx.send_modal(modal)

"""
#RUN
try:    
    bot.run(os.getenv('BOT_TOKEN'))
except Exception as e:
    print(f"Erreur: {e}")
"""

bot.run(os.getenv('BOT_TOKEN'))