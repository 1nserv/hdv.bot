import discord
from discord.ext import commands

import nsarchive as nsa
from nsarchive.models.base import *

from bot.utils import *
from bot import embeds
from bot.views import votes as vw

class VotesCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    vote_cmds = discord.SlashCommandGroup(name = "votes")

    @commands.slash_command(name = "vote")
    async def vote(self, ctx: discord.ApplicationContext, vote: str):
        await ctx.defer()
        _vote = NSID(vote)

        user = entities.get_entity(NSID(ctx.author.id))

        vote: nsa.Vote = state.alias(user.id).get_vote(_vote)
        try:
            election: nsa.Election = state.alias(user.id).get_election(_vote)
        except:
            election = None

        if not vote:
            await ctx.send_followup(f"Le vote {_vote} n'existe pas.")
            return

        await ctx.send_followup(embed = embeds.votes.voteProposalsEmbed(vote, election), view = vw.ManageVoteView(vote, user), ephemeral = True)

    @vote_cmds.command(name = "open")
    async def open_vote(self, ctx: discord.ApplicationContext):
        await ctx.send_modal(vw.OpenVoteModal())


def setup(bot):
    bot.add_cog(VotesCog(bot))