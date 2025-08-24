import time

import discord

import nsarchive as nsa
from nsarchive import mandate

from .func import *
from bot import settings


def voteProposalsEmbed(vote: nsa.Vote) -> discord.Embed:
    __types = {
        'normal': "Normal",
        'full': "Présidentielles",
        'partial': "Législatives",
        '2pos': "Pour/Contre",
        '3pos': "Pour/Contre/Blanc"
    }
    __started = vote.start_date <= time.time()
    __closed = vote.end_date <= time.time()

    title = "Vote terminé" if __closed else vote.title

    if __started or __closed:
        __date_label = "Fin"
        __date_value = vote.end_date
    else:
        __date_label = "Début"
        __date_value = vote.start_date

    _count: str = lambda c: f" - **{c:,} votes**".replace(',', ' ') if __closed else ""

    _proposals = '\n'.join([ f"- {opt.title}{_count(opt.count)}" for opt in vote.options.values() ])

    description = f"""
    **Auteur:** <@{int(vote.author, 16)}>
    **Type:** {__types[vote.type]}
    **{__date_label}:** <t:{__date_value}:f>
    """

    if len(vote.options) > 0:
        description += f"""
        ### Options
        {_proposals}
        """

    return discord.Embed(
        title = title,
        description = noTab(description),
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Vote n°{vote.id}")
    )

def voteSubmittedEmbed(vote: nsa.Vote, options: list[nsa.VoteOption]) -> discord.Embed:
    return discord.Embed(
        title = ":white_check_mark: Vote enregistré",
        description = f"Vous avez voté pour les options suivantes:\n- " + "\n- ".join([ opt.title for opt in options ]),
        color = settings.BOT_COLOR,
        footer = discord.EmbedFooter(f"Vote n°{vote.id}")
    )