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
    async def vote(self, ctx: discord.ApplicationContext, vote: str, ephemeral: bool | None = True):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /vote")
        try:
            await ctx.defer()
            _vote = NSID(vote)

            user = entities.get_user(NSID(ctx.author.id))

            vote: nsa.Vote = state.get_vote(_vote)

            if not vote:
                await ctx.send_followup(f"Le vote {_vote} n'existe pas.")
                return

            if vote.type in ('partial', 'full'):
                await ctx.send_followup(embed = embeds.votes.electionProposalsEmbed(vote), view = vw.ManageVoteView(vote, user if ephemeral else None), ephemeral = ephemeral)
            else:
                await ctx.send_followup(embed = embeds.votes.voteProposalsEmbed(vote), view = vw.ManageVoteView(vote, user if ephemeral else None), ephemeral = ephemeral)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @vote_cmds.command(name = "open")
    async def open_vote(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /open")
        try:
            await ctx.send_modal(vw.OpenVoteModal())
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)


def setup(bot):
    bot.add_cog(VotesCog(bot))