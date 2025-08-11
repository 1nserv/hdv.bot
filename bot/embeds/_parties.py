import discord

import nsarchive as nsa

from .func import *
from bot import settings


def welcomeEmbed(party: nsa.Organization):
    title = f"Salon général de {party.name}"
    description = f"""Ce salon est accessible par tous les membres du parti.
    Ici, vous pouvez parler de tout et de rien: vous êtes là pour vous réunir entre membres du même parti !
    Bonne discussion !.
    """

    color = settings.BOT_COLOR
    footer = discord.EmbedFooter(f"Parti n°{party.id}")

    return discord.Embed(title = title, description = noTab(description), color = color, footer = footer)

def partyCreatedEmbed(party: nsa.Organization) -> discord.Embed:
    title = f"{party.name} a été crée !"
    description = f"""En ce jour du <t:{party.register_date}:d>, votre parti a été créé avec succès par {party.owner.name}.

    Pour l'instant, votre parti est encore considéré comme un simple groupe. Voici les étapes pour l'activer:
    1. Regrouper {settings.MIN_PARTY_MEMBERS} membres
    2. Exécuter la commande `/panel`
    3. Presser le bouton "Enregistrer mon parti"
    4. Renseigner les infos
    """

    color = settings.BOT_COLOR
    footer = discord.EmbedFooter(f"Parti n°{party.id}")

    embed = discord.Embed(title = title, description = noTab(description), color = color, footer = footer)

    return embed

def partyCreated_LOG(party: nsa.Organization, promotion_text: str) -> discord.Embed:
        promotion_text = "\n".join(f"> {line}" for line in promotion_text.splitlines())

        title = f"{party.owner.name} a crée le parti: {party.name}"
        if len(promotion_text) != 0: 
            description = f"""
            ### Discours de promotion

            {promotion_text}

            **Vous pouvez rejoindre ce parti en executant la commande `/group join`.**
            N'oubliez pas de spécifier l'ID du parti: `{party.id}`

            Pour obtenir des informations sur celui-ci, vous pouvez exécuter la commande `/party info`.
            """
        else:
            description = f"""
            Aucun discours de promotion n'a été fourni.

            **Vous pouvez rejoindre ce parti en executant la commande `/group join`.**
            N'oubliez pas de spécifier l'ID du parti: `{party.id}`

            Pour obtenir des informations sur celui-ci, vous pouvez exécuter la commande `/party info`.
            """

        color = settings.BOT_COLOR
        footer = discord.EmbedFooter(f"Parti n°{party.id}")

        return discord.Embed(title = title, description = noTab(description), color = color, footer = footer)


def memberJoinedEmbed(author: discord.Member, party: nsa.Organization) -> discord.Embed:
    title = "Nouveau membre"
    description = f"{author.mention} a rejoint votre parti !"

    color = settings.BOT_COLOR
    footer = discord.EmbedFooter(f"Parti n°{party.id}")

    return discord.Embed(title = title, description = noTab(description), color = color, footer = footer)

def inAnotherPartyEmbed() -> discord.Embed:
    return discord.Embed(
        title = "**:x: Vous appartenez déjà à un parti !**",
        color = discord.Color.brand_red()
    )

def alreadyInPartyEmbed() -> discord.Embed:
    return discord.Embed(
        title = "**:warning: Vous appartenez déjà à ce parti.**",
        color = settings.BOT_COLOR
    )
