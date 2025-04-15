import discord
from discord.ext import commands
import bot.settings as settings

import nsarchive

import re

import io
import aiohttp

on_course = []

class bot_functions():
    def __init__(self, bot):
        self.bot = bot
    
    def transform_channel_name(name: str) -> str:
        name = re.sub(r'\s+', '-', name)
        name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
        return name.lower()
    
    async def get_logo(ctx: discord.ApplicationContext | discord.Interaction, party: nsarchive.Organization):
        trash_channel: discord.TextChannel = ctx.guild.get_channel(settings.trash_channel_id)
            
        image_stream = io.BytesIO(party.avatar)
        discord_file = discord.File(fp=image_stream, filename="image.jpg")
        
        await trash_channel.send(file=discord_file)
            
        history = await trash_channel.history(limit=1).flatten()
        last_message = history[0]
        return last_message.attachments[0].url
    
    async def get_byte_stream(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Erreur lors du téléchargement de l'image : {response.status}")
                
    def start_task(user: discord.User):
        on_course.append(user.id)
    def end_task(user: discord.User):
        on_course.remove(user.id)
        
    def is_admin(ctx: discord.ApplicationContext) -> bool:
        admin_role = ctx.guild.get_role(settings.admin_role_id)
        return admin_role in ctx.user.roles
    
    def is_citoyen(user: nsarchive.User) -> bool:
        return user.get_level() >= settings.min_level_to_citoyen