import aiohttp
import dotenv
from collections import Counter
from datetime import datetime
import io
import os
from PIL import Image
import re

dotenv.load_dotenv(override = True)


import discord

import nsarchive as nsa

entities = nsa.EntityInterface(os.getenv('APP_URL'), os.getenv('API_KEY'))
state = nsa.StateInterface(os.getenv('APP_URL'), os.getenv('API_KEY'))


from bot import settings

on_course = []

def get_primary_color(img: io.BytesIO, top_n = 5) -> int:
    image = Image.open(img)
    image = image.convert("RGB")
    pixels = list(image.getdata())

    color_counts = Counter(pixels)
    most_common = color_counts.most_common(top_n)
    result = sorted(most_common, key = lambda c : -c[1])
    result: int = [ c[0] for c in result ]

    for color in result:
        if not(all(c >= 240 for c in color) or all(c <= 32 for c in color)): # On exclut la couleur de fond si elle ne sert à rien
            final = color
    else:
        final = result[0]

    r, g, b = final
    return (r << 16) + (g << 8) + b

def get_ts(val: str) -> int:
    if " " in val:
        dt = datetime.strptime(val, "%Y-%m-%d %H:%M:%S" if val.count(":") == 2 else "%Y-%m-%d %H:%M")
    else:
        dt = datetime.strptime(val, "%Y-%m-%d")

    return int(dt.timestamp())

def get_dt(val: str) -> int:
    val = val.replace(' ', '')

    quantity = ''
    unit = ''

    units = {
        's': 1,
        'min': 60,
        'h': 3600,
        'd': 86400,
        'w': 608400,
        'cy': 2419200, # Cycle = 28j
        'mo': 2592000, # Mois = 30j
        'm': 2592000, # Idem
        'y': 31536000, # Année = 365j
        'yr': 31536000, # Idem
        'an': 31536000 # Idem
    }

    for l in val:
        if l.isdigit():
            if unit != '': # On évite les dingueries du style "1d25"
                raise ValueError('Letter expected')
            else:
                quantity += l
        else:
            if quantity == '': # Un nombre est obligatoire
                raise ValueError('Number expected')
            else:
                unit += l

    try:
        return int(quantity) * units[unit]
    except KeyError:
        raise ValueError('Unit not recognized')



def transform_channel_name(name: str) -> str:
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
    return name.lower()

async def get_logo(ctx: discord.ApplicationContext | discord.Interaction, party: nsa.Organization):
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

def is_citoyen(user: nsa.User) -> bool:
    return user.get_level() >= settings.min_level_to_citoyen