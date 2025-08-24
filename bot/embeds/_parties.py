import discord

import nsarchive as nsa

from .func import *
from bot import settings


def partyListEmbed(parties: list[tuple[nsa.Organization, nsa.Party | None]]):
    description = ""

    for group, party in parties:
        _content = f"""
        **Président:** <@{int(group.owner.id, 16)}>
        **Membres:** {len(group.members) + 1}
        **Date de création:** <t:{group.register_date}:d>
        """

        if party:
            _content += f"""
            **Couleur:** `#{hex(party.color)[2:].upper()}`
            **Devise:** _“{party.motto}”_
            """.lstrip('\n')
        else:
            _content += "_Parti non enregistré._"

        description += f"""
        ## {group.name}
        {_content}
        """

    if description == "":
        description = "_Aucun parti sur le serveur._"

    return discord.Embed(
        title = "Liste des partis",
        description = description,
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Vie politique")
    )

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

    Vous pouvez maintenant devenir candidat à une élection en suivant ces étapes:
    1. Regrouper {settings.MIN_PARTY_MEMBERS} membres (si ce n'est pas déjà fait)
    2. Exécuter la commande `/panel`
    3. Presser le bouton "Se présenter"
    4. Renseigner l'ID de l'élection visée (consulter un administrateur si besoin)
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

def partyTransmittedEmbed(party: nsa.Organization):
    return discord.Embed(
        title = "Changement de président",
        description = f"<@{int(party.owner.id, 16)}> est désormais président.e du parti.",
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Parti n°{party.id}")
    )

def partyRenamedEmbed(party: nsa.Organization):
    return discord.Embed(
        title = "Changement de nom",
        description = f"Le parti s'appelle maintenant {party.name}",
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Parti n°{party.id}")
    )

def partyDeletedEmbed(party: nsa.Organization):
    return discord.Embed(
        title = "Parti supprimé",
        description = f"Le parti {party.name} n'existe plus.",
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Parti n°{party.id}")
    )


def memberJoinedEmbed(author: discord.Member, party: nsa.Organization) -> discord.Embed:
    title = "Nouveau membre"
    description = f"{author.mention} a rejoint votre parti !"

    color = settings.BOT_COLOR
    footer = discord.EmbedFooter(f"Parti n°{party.id}")

    return discord.Embed(title = title, description = noTab(description), color = color, footer = footer)

def memberLeftEmbed(author: discord.Member, party: nsa.Organization) -> discord.Embed:
    title = "Départ d'un membre"
    description = f"{author.mention} a quitté le parti."

    color = settings.BOT_COLOR
    footer = discord.EmbedFooter(f"Parti n°{party.id}")

    return discord.Embed(title = title, description = noTab(description), color = color, footer = footer)


def inAnotherPartyEmbed(third_person: bool = False) -> discord.Embed:
    return discord.Embed(
        title = f"**:x: {'Ce membre appartient' if third_person else 'Vous appartenez'} déjà à un parti !**",
        color = discord.Color.brand_red()
    )

def alreadyInPartyEmbed(third_person: bool = False) -> discord.Embed:
    return discord.Embed(
        title = f"**:information_source: {'Ce membre appartient' if third_person else 'Vous appartenez'} déjà au parti.**",
        color = settings.BOT_COLOR
    )

def notInAnyPartyEmbed(third_person: bool = False) -> discord.Embed:
    return discord.Embed(
        title = f"**:x: {'Ce membre appartient' if third_person else 'Vous appartenez'} à aucun parti.**",
        color = discord.Color.brand_red()
    )