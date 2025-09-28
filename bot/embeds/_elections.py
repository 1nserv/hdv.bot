import time

import discord

import nsarchive as nsa
from nsarchive import mandate

from .func import *
from bot import settings


def panelEmbed(user: nsa.User, group: nsa.Organization | None, candidate: nsa.Candidate | None) -> discord.Embed:
    party = candidate.party if candidate else None
    title = f"Panel de {user.name}"

    description = f"""
    **Parti:** {group.name if group else 'Aucun'}
    **Candidature:** {f"`{candidate.current}`" if candidate and candidate.current else "Aucune"}
    ### Infos du cycle
    **Cycle actuel:** Cycle n°{mandate.get_cycle() + 1}
    **Législatives:** <t:{mandate.next_election()}:D>
    **Présidentielles:** <t:{mandate.next_election('full')}:D>
    """

    if group:
        description += f"""
        ### Infos du parti
        **NSID:** `{group.id}`
        **Nom:** {group.name}
        **Président:** {group.owner.name}
        **Devise:** {party.motto if party else "Non fournie"}
        **Couleur:** {"`#" + hex(party.color)[2:].upper() + "`" if party else "Non fournie"}
        **Membres:** {len(group.members) + 1}
        """

    color = party.color if party else settings.BOT_COLOR

    return discord.Embed(
        title = title,
        description = noTab(description),
        color = color
    )


def candidateInfoEmbed(
        candidate: nsa.Candidate,
        user: nsa.User,
        profile: discord.Member,
        group: nsa.Organization,
    ) -> discord.Embed:

    description = f"""
    **Membre:** {profile.mention}
    **Groupe:** {group.name}
    **Candidature:** {f"`{candidate.current}`" if candidate and candidate.current else "Aucune"}
    """

    embed = discord.Embed(
        title = f"Nouveau candidat: {user.name}",
        description = description,
        color = candidate.party.color
    )

    return embed.set_thumbnail(url = profile.avatar.url)



def candidacySubmittedEmbed(party: nsa.Party):
    return discord.Embed(
        description = ":white_check_mark: Votre candidature est retenue !",
        color = party.color
    )

def newCandidateEmbed(
        vote: nsa.Vote,
        group: nsa.Organization,
        user: nsa.User,
        candidate: nsa.Candidate,
        profile: discord.Member,
        speech: str = None
    ) -> discord.Embed:

    if speech:
        _speech = "“" + speech.replace('\n', ' ') + "”"
    else:
        _speech = "Aucun discours prononcé."

    description = f"""
    {profile.mention}, candidat.e du groupe **{group.name}**, souhaite se présenter aux prochaines élections {"présidentielles" if vote.type == "full" else "législatives"}.

    > {_speech}
    """

    embed = discord.Embed(
        title = f"Nouveau candidat: {user.name}",
        description = description,
        color = candidate.party.color,
        footer = discord.EmbedFooter(f"Élection n°{vote.id}")
    )

    return embed.set_thumbnail(url = profile.avatar.url)


def elTypePresentationEmbed() -> discord.Embed:
    description = """
    **Présidentielles:** Les élections présidentielles permettent d'élire le Président de la République. Elles ont lieu tous les 56 jours (2 cycles)
    **Législatives:** Les élections législatives nomment les députés qui siégeront à l'Assemblée Nationale. Elles ont lieu tous les 28 jours (1 cycle)
    """

    return discord.Embed(
        title = "Choisissez un type d'élections",
        description = noTab(description),
        color = settings.BOT_COLOR
    )

def elPlannedEmbed(vote: nsa.Vote) -> discord.Embed:
    __type = "Présidentielles" if vote.type == "full" else "Législatives"

    description = f"""
    **Type:** {__type}
    **ID de l'élection:** `{vote.id}` (nécessaire pour se présenter)

    **Vote associé:** `{vote.id}` (nécessaire pour voter)
    **Début:** <t:{vote.start_date}:f>
    **Fin:** <t:{vote.end_date}:f>
    """

    return discord.Embed(
        title = ":white_check_mark: Nouvelles élections planifiées",
        description = noTab(description),
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter("Vie politique")
    )