import time

import discord

import nsarchive as nsa
from nsarchive import mandate

from .func import *
from bot import settings


def voteProposalsEmbed(vote: nsa.Vote, election: nsa.Election = None) -> discord.Embed:
    __started = vote.startDate <= time.time()
    __closed = vote.endDate <= time.time()

    title = "Vote terminé" if __closed else vote.title

    if __started or __closed:
        __date_label = "Fin"
        __date_value = vote.endDate
    else:
        __date_label = "Début"
        __date_value = vote.startDate

    _proposals = '\n'.join([ f"- {opt.title}" + (f" - **{opt.count:,} votes**".replace(',', ' ') if __closed else "") for opt in vote.options.values() ])

    description = f"""
    **Auteur:** <@{int(vote.author, 16)}>
    **Type:** {"Vote" if not election else "Présidentielles" if election.type == 'full' else "Législatives"}
    **{__date_label}:** <t:{__date_value}:f>

    ### Options
    {_proposals}
    """

    return discord.Embed(
        title = title,
        description = noTab(description),
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Vote n°{vote.id}")
    )

def voteSubmittedEmbed(vote: nsa.Vote, option: nsa.VoteOption) -> discord.Embed:
    return discord.Embed(
        title = ":white_check_mark: Vote enregistré",
        description = f"Vous avez voté pour l'option **{option.title}**.",
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Vote n°{vote.id}")
    )