import discord
import bot.settings as settings
import nsarchive
from datetime import datetime

class Bot:
    def not_acess(interaction: bool = False) -> discord.Embed:
        if interaction:
            title = "**❌ Vous n'avez pas l'autorisation d'intéragir.**"
        else:
            title = "**❌ Vous n'avez pas accès à cette commande.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def success() -> discord.Embed:
        title = "**✅ Opération réussie !**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def failure() -> discord.Embed:
        title = "**❌ L'opération a échoué.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def cancel() -> discord.Embed:
        title = "**❌ L'opération a été annulée.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def not_citoyen() -> discord.Embed:
        title = f"**❌ Vous n'êtes pas citoyen ! Attendez d'obtenir le niveau {settings.min_level_to_citoyen}.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
class Parties:
    def no_parties() -> discord.Embed:
        title = "**❌ Aucun parti n'est enregistré sur le serveur.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def you_are_not_in_a_party() -> discord.Embed:
        title = "**❌ Vous ne faites partie d'aucun parti.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def party_not_found() -> discord.Embed:
        title = "**❌ Ce parti n'existe plus.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def parties_list_embed(parties_list: list)-> discord.Embed:
        title = "**Liste des partis du serveur**"
        description = "\n".join(f"\\- {entity}" for entity in parties_list) # type: ignore
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        return embed
    
    def party_deleted_cause_no_members(party_name: str) -> discord.Embed:
        title = f"**:white_check_mark: Vous avez quitté {party_name} avec succès ! Puisque vous étiez le dernier membre, il a été supprimé.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def cant_leave_while_president() -> discord.Embed:
        title = "**:x: Vous ne pouvez pas quitter ce parti tant que vous êtes son président ! Nommez un nouveau président pour quitter.**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def already_in_party() -> discord.Embed:
        title = "**❌ Vous appartenez déjà à un parti !**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def you_are_already_in_this_party() -> discord.Embed:
        title = "**❌ Vous appartenez déjà à ce parti !**"
        color = settings.bot_color
        embed = discord.Embed(title = title, color = color)
        return embed
    
    def party_created_in_infos(name: str, ts: int, owner:discord.User | discord.Member, promotion_text: str) -> discord.Embed:
        promotion_text = "\n".join(f"> {line}" for line in promotion_text.splitlines())
        
        title = f"{owner.display_name} a crée le parti: {name}"
        if len(promotion_text) != 0: 
            description = f'''Ce parti doit atteindre {settings.min_members_to_become_active} membres avant le <t:{ts}:f> (<t:{ts}:R>) pour pouvoir s'activer.
Voici le texte de promotion donné par le créateur ({owner.mention}):
        
{promotion_text}

**Vous pouvez rejoindre ce parti en executant la commande `/join_party`.**
N'oubliez pas de spécifier le nom du parti : {name}

Pour obtenir des informations sur celui-ci, vous pouvez exécuter la commande `/party_infos`.
        
'''
        else:
            description = f'''Ce parti doit atteindre {settings.min_members_to_become_active} membres avant le <t:{ts}:f> (<t:{ts}:R>) pour pouvoir s'activer.

**Vous pouvez rejoindre ce parti en executant la commande `/join_party`.**
N'oubliez pas de spécifier le nom du parti : {name}

Pour obtenir des informations sur celui-ci, vous pouvez exécuter la commande `/party_info`.
        
'''   
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=owner.avatar.url)
        
        return embed
    def party_expired(name:str, members: list, url):
        title = "Un parti a été supprimé ! :x:"
        description = f'''Le parti nommé {name} a été supprimé.

En effet, ce parti n'a pas réussi à atteindre le nombre fatidique de {settings.min_members_to_become_active} membres pour passer dans la catégorie très prisée des partis actifs.

Tous les membres ayant rejoint ce parti entre la date de création et aujourd'hui sont automatiquement expulsés. Voici la liste des membres concernés:

> {[member.name for member in members]}

'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        return embed

    def LastMember(name:str, url):
        title = "Un parti a été supprimé ! :x:"
        description = f'''Le parti nommé {name} a été supprimé.

En effet, le dernier membre ayant quitté le parti, celui-ci s'est auto-détruit.

'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        return embed
    
    def party_info(ctx: discord.Interaction, party: nsarchive.Organization, url):
    
        owner: discord.Member = ctx.guild.get_member(int(party.owner.id, 16))
        date_time = datetime.fromtimestamp(party.registerDate)
        date_str = date_time.strftime("%d/%m/%Y")
        
        title = f"{party.name}"
        description = f'''      
**Président:** {owner.mention}
**Secrétaire général:**
        
**Nombre de membres:** {len(party.members)}
        
        
Pour rejoindre ce parti, veuillez éxécuter la commande `/join_party`.
'''
        color = settings.bot_color
        footer = discord.EmbedFooter(f"Parti crée le {date_str}")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        return embed
    
    def join():
        title = "Rejoindre un parti ?"
        description = f'''
Vous pouvez rejoindre un des partis dans la liste ci-dessous.
Vous ne pourrez pas le quitter pendant 24h.

Si vous voulez annuler, appuyez sur "rejeter ce message".
'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        from main import bot
        
        embed.set_thumbnail(url=bot.user.avatar.url)
        return embed

class InParties:
    
    def party_created(name: str, ts: int, date: str, owner:discord.User | discord.Member) -> discord.Embed:
        title = f"{name} a été crée !"
        description = f'''En ce jour du {date}, votre parti a été crée avec succès par {owner.display_name}.

Cependant, pour valider sa création et activer ce parti, vous devez atteindre {settings.min_members_to_become_active} membres avant le <t:{ts}:f> (<t:{ts}:R>).
Si ce n'est pas le cas, ce parti sera automatiquement détruit.
        
Par défaut, le logo du parti est celui du créateur ({owner.mention}), mais le président peut le changer avec la commande `/party_config`.'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        # from main import bot
        
        # embed.set_thumbnail(url=bot.user.avatar.url)
        return embed
    
    def general_embed(name:str, owner: discord.User | discord.Member):
        title = f"Bienvenue dans le salon général de {name}"
        description = f'''Ce salon est accessible par tous les membres du parti.

Ici, vous pouvez parler de tout et de rien : vous êtes là pour vous réunir entre membres du même parti !
Bonne discussion !.

'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        
        # embed.set_thumbnail(url=bot.user.avatar.url)
        return embed
    
    def activity_thread():
        title = f"Bienvenue dans le salon activité !"
        description = f'''C'est ici que les arrivées et les départs seront tenus à jour.
'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        # from main import bot
        
        # embed.set_thumbnail(url=bot.user.avatar.url)
        return embed
    
    def member_joined(author: discord.User | discord.Member) -> discord.Embed:
        title = " "
        description= f"{author.mention} a rejoint votre parti !"
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description=description, color = color, footer = footer)
        embed.set_thumbnail(url=author.avatar.url)
        
        return embed
    
    def member_leaved(author: discord.User | discord.Member) -> discord.Embed:
        title = " "
        description= f"{author.mention} a quitté votre parti !"
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description=description, color = color, footer = footer)
        embed.set_thumbnail(url=author.avatar.url)
        
        return embed

    def new_party_name_private(party_name: str):  
        title = f"Votre parti change de nom !"
        description = f'''      
Et oui ! Le nouveau nom de votre parti est : {party_name}.
'''
        color = settings.bot_color
        footer = discord.EmbedFooter(f"Parti modifié par votre président.")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        from main import bot
        
        embed.set_thumbnail(url=bot.user.avatar.url)
        return embed

    def new_party_name_public(last_party: nsarchive.Organization, new_party: nsarchive.Organization, url):  
        title = f"Un parti change de nom !"
        description = f'''      
Après maintes discussions, la présidence du parti nommé "{last_party.name}" a décidé d'évoluer.

En effet ce parti change d'identité et adopte ce nouveau nom: {new_party.name}
'''
        color = settings.bot_color
        footer = discord.EmbedFooter(f"Vie Politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        return embed

    def new_party_logo_private(url):  
        title = f"Votre parti change d'identité visuelle !"
        description = f'''      
Et oui ! Le nouveau logo de votre parti est affiché ci-dessous.
'''
        color = settings.bot_color
        footer = discord.EmbedFooter(f"Parti modifié par votre président.")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        
        from main import bot
        
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_image(url=url)
        return embed

    def new_party_logo_public(url, party: nsarchive.Organization):  
        title = f"Un parti change d'identité visuelle !"
        description = f'''      
Le parti nommé "{party.name} adopte un nouveau logo, après décision du président.
Le nouveau logo est ci-dessous. Dites-leurs ce que vous en pensez !"
'''
        color = settings.bot_color
        footer = discord.EmbedFooter(f"Vie Politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        embed.set_image(url=url)
        return embed
    
class President:

    def Config(url):
        title = "Modifier le parti ?"
        description = f'''
Voici les options vous étant accessible:

- Renommer le parti: changer le nom de votre parti (vous ne pourez plus le faire pendant 2 mois)

- Changer l'icône: changer le logo de votre parti (vous ne pourez plus le faire pendant 1 semaine)

- Nommer un secrétaire général (son mandat est de 2 semaines minimum)

- Nommer jusqu'à 2 portes-paroles (changeable toutes les deux semaines)

- Nommer des journalistes qui s'occuperont des médias de votre parti ({settings.number_of_journalists} membres maximum. Changeable toutes les 2 semaines)
'''
        color = settings.bot_color
        footer = discord.EmbedFooter("vie politique")
        embed = discord.Embed(title = title, description = description, color = color, footer = footer)
        embed.set_thumbnail(url=url)
        return embed