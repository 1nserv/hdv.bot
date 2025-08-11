import time

import discord

import nsarchive as nsa
from nsarchive import mandate

from .func import *
from bot import settings


def panelEmbed(user: nsa.User, group: nsa.Organization | None, party: nsa.Party | None) -> discord.Embed:
    title = f"Panel de {user.name}"

    description = f"""
    **Parti:** {group.name if group else 'Aucun'}{' (non enregistré)' if group and not party else ''}
    ### Infos du cycle
    **Cycle actuel:** {mandate.get_cycle() + 1}
    **Prochaines élections:** <t:{round(time.time()) + 86400 * ((28 - mandate.get_day()) % 28)}:f>
    **Présidentielles:** <t:{round(time.time()) + 86400 * ((56 - mandate.get_day()) % 56)}:f>
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

def elPlannedEmbed(election: nsa.Election, vote: nsa.Vote) -> discord.Embed:
    __type = "Présidentielles" if election.type == "full" else "Législatives"

    description = f"""
    **Type:** {__type}
    **ID de l'élection:** `{election.id}` (nécessaire pour se présenter)

    **Vote associé:** `{vote.id}` (nécessaire pour voter)
    **Début:** <t:{vote.startDate}:f>
    **Fin:** <t:{vote.endDate}:f>
    """

    return discord.Embed(
        title = ":white_check_mark: Nouvelles élections planifiées",
        description = noTab(description),
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter("Vie politique")
    )