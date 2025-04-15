import discord
from discord.ext import commands
import time
from datetime import datetime
import bot.embeds as embeds

import nsarchive
from nsarchive import Organization
import bot.settings as settings
from functions import bot_functions as functions

import time
import io
from PIL import Image
from bot.utils import entities
from bot import utils

class party_functions():     
    def get_parties_names(lower: bool = False, but_except: str = None) -> list:
        parties = entities.fetch_entities(position='parti')
        if lower:
            if len(parties) != 1:
                return [party.name.lower() for party in parties if party.name != but_except]
            else:
                return [party.name.lower() for party in parties]
        else:
            if len(parties) != 1:
                return [party.name for party in parties if party.name != but_except]
            else:
                return [party.name for party in parties]

    async def create_party(name, promotion_text, author: discord.User | discord.Member):
        user_id = nsarchive.NSID(author.id)
        entity = entities.get_entity(user_id)

        # Détermination de la couleur du rôle

        img_color = utils.get_primary_color(io.BytesIO(await functions.get_byte_stream(author.avatar.url)))
        print(img_color)

        # Création du rôle

        party_role: discord.Role = await author.guild.create_role(
            name = name,
            hoist = True,
            mentionable = False,
            color = discord.Color(img_color)
        )

        await party_role.edit(position=author.guild.get_role(settings.order_force_role_id).position - 1)
        await author.add_roles(party_role, author.guild.get_role(settings.party_chief_role_id))

        # Création du parti chez NationDB

        party = Organization(nsarchive.NSID(party_role.id))
        party.name = name
        party.position = entities.get_position("parti")
        party.owner = entity
        party.members.append(nsarchive.GroupMember(user_id))
        party.registerDate = int(time.time())
        party.avatar = await functions.get_byte_stream(author.avatar.url)

        entities.save_entity(party)

        party = entities.get_entity(nsarchive.NSID(party_role.id)) # Permet que l'instance soit initlalisée correctement
        # party.add_certification("parti non certifié")

        # Création du thread du Parti
        party_category = author.guild.get_channel(settings.party_category_id)
        party_infos_channel = author.guild.get_channel(settings.party_infos_channel_id)
        party_forum: discord.ForumChannel = await party_category.create_forum_channel(name=name, position=2)

        overwrite = {
            author.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            party_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        for role, perms in overwrite.items():
            await party_forum.set_permissions(role, overwrite=perms)

        party.additional["channel_id"] = party_forum.id
        
        current_date = datetime.now()
        date = f"{current_date.day} {settings.months[current_date.month - 1]} {current_date.year}"
        end_date = round(time.time()) + (24 * 3600)

        await party_forum.create_thread("général", content=party_role.mention, embed=embeds.InParties.general_embed(name, author))

        infos = await party_forum.create_thread("informations", content=party_role.mention, embed=embeds.InParties.party_created(name, end_date, date, author))
        await infos.edit(pinned=True, locked=True)

        arrivals = await party_forum.create_thread("activité", content=party_role.mention, embed=embeds.InParties.activity_thread())
        await arrivals.edit(locked=True)

        return await party_infos_channel.send(embed=embeds.Parties.party_created_in_infos(name, end_date, author, promotion_text))

    async def join_party(interaction: discord.Interaction, party:Organization):   
        
        player_nsid= nsarchive.NSID(interaction.user.id)
        entity = entities.get_entity(player_nsid)        
        entity_groups = entity.groups()
        
        for org in entity_groups:
            if str(org.position).upper() == "PARTI":
                if org.name == party.name:
                    return await interaction.respond(embed = embeds.Parties.you_are_already_in_this_party(), ephemeral = True)   
                else:
                    return await interaction.respond(embed = embeds.Parties.already_in_party(), ephemeral = True)
            
        party_role = interaction.guild.get_role(int(party.id, 16))
                
        await interaction.user.add_roles(party_role)
            
        member = nsarchive.GroupMember(player_nsid)

        party.add_member(member)
        entities.save_entity(party)
        
        party_channel = interaction.guild.get_channel(party.additional["channel_id"])
        party_thread = None
        for thread in party_channel.threads:
            if thread.name == "activité":
                party_thread = thread
                
        if party_thread == None:
            print(f"Impossible de retrouver le thread info de {party.name}")
        else:
            await party_thread.send(embed=embeds.InParties.member_joined(interaction.user), content=interaction.user.mention)
        
        return await interaction.respond(embed = embeds.Bot.success(), ephemeral = True) 
    
    async def delete_party(ctx:discord.ApplicationContext, party:nsarchive.Organization, reason: str):

        party_chan = discord.utils.get(ctx.guild.forum_channels, name = functions.transform_channel_name(party.name))
        
        if party_chan:
            await party_chan.delete()

        role: discord.Role = ctx.guild.get_role(int(party.id, 16))
        party_chief_role = ctx.guild.get_role(settings.party_chief_role_id)
        if role:
            for member in role.members:
                    if party_chief_role in member.roles:
                        await member.remove_roles(party_chief_role)
            await role.delete()

        party_infos_channel = ctx.guild.get_channel(settings.party_infos_channel_id)
        member_list = party.members
        if len(member_list) == 0:
            member_list = ""

        entities.delete_entity(party)
        
        if reason == "pre_party_time_expired":
            return await party_infos_channel.send(embed = embeds.Parties.party_expired(party.name, member_list, await functions.get_logo(ctx, party)))
        if reason == "last_member":
            return await party_infos_channel.send(embed = embeds.Parties.LastMember(party.name, await functions.get_logo(ctx, party)))
        
    async def rename(interaction: discord.Interaction, party:Organization, new_name):
        last_party = party
        party.set_name(new_name=new_name)
        entities.save_entity(party)
        
        party_role = interaction.guild.get_role(int(party.id, 16))
        await party_role.edit(name=new_name)
        return await party_functions.update_party_channel(interaction, last_party, party)
    
    async def update_party_channel(interaction: discord.Interaction, past_party: Organization, now_party: Organization, ):      
         
        import bot.embeds as embeds
        
        party_channel = interaction.guild.get_channel(past_party.additional["channel_id"])
        party_role = interaction.guild.get_role(int(past_party.id, 16))
        party_infos_channel = interaction.guild.get_channel(settings.party_infos_channel_id)
        
        party_thread = None
        for thread in party_channel.threads:
            if thread.name == "informations":
                party_thread = thread
        
        if party_thread == None:
            return print(f"Impossible de trouver le thread Informations pour {past_party.name}.")
        
        party_logo_url = await functions.get_logo(interaction, now_party)
        
        await interaction.response.send_message(embed=embeds.Bot.success(), ephemeral=True)
        
        if past_party.name != now_party: 
            await party_channel.edit(name=now_party.name)
            await party_thread.send(embed=embeds.InParties.new_party_name_private(now_party.name), content=party_role.mention)
            await party_infos_channel.send(embed=embeds.InParties.new_party_name_public(past_party, now_party, party_logo_url))
            
        if past_party.avatar != now_party.avatar:
            await party_channel.edit(name=now_party.name)
            await party_thread.send(embed=embeds.InParties.new_party_logo_private(party_logo_url), content=party_role.mention)
            await party_infos_channel.send(embed=embeds.InParties.new_party_logo_public(party_logo_url, now_party))
    
    async def change_logo(ctx: discord.ApplicationContext, interaction: discord.Interaction, party: Organization):     
        import bot.embeds as embeds
        functions.start_task(interaction.user)
        
        last_party = party
            
        await interaction.response.send_message(embed=embeds.LogoChange(party.name, await functions.get_logo(interaction, party)), ephemeral = True)
        def check(m):
            return m.author == interaction.user and m.channel.id == interaction.channel.id
        try:
            
            from main import bot
            
            reply: discord.Message = await bot.wait_for('message', check=check, timeout=600)  # 10 minutes
            if reply.content.lower() == "stop":
                functions.end_task(interaction.user)
                await reply.delete()
                return await ctx.respond(embed=discord.Embed(), ephemeral=True)

            if not reply.attachments:
                functions.end_task(interaction.user)
                return await ctx.respond(embed=discord.Embed(), ephemeral=True)
                
            mess2: discord.Message = await reply.reply(embed=discord.Embed())
                
            img = reply.attachments[0]
            img_data = await img.read()

            # Ouvrir l'image avec Pillow
            img = Image.open(io.BytesIO(img_data))
            min_dim = min(img.size)

            left = (img.width - min_dim) / 2
            top = (img.height - min_dim) / 2
            right = (img.width + min_dim) / 2
            bottom = (img.height + min_dim) / 2

            img_cropped = img.crop((left, top, right, bottom))

            img_bytes = io.BytesIO()
            img_cropped.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            party.avatar = img_bytes
            entities.save_entity(party)
                
            await reply.delete()
            await mess2.delete()
            functions.end_task(interaction.user)
            await party_functions.update_party_channel(interaction, last_party, party)
            return await ctx.respond(embed=discord.Embed(), ephemeral=True)
        except:
            return