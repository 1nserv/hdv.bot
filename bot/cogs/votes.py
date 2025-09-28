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
            await ctx.defer(ephemeral = ephemeral)
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

    @vote_cmds.command(name = "results")
    async def apply_vote(self, ctx: discord.ApplicationContext, id: str):
        log(f"{ctx.author.name} ({NSID(ctx.author.id)}) utilise /results")
        try:
            author = entities.get_user(NSID(ctx.author.id))
            vote = state.get_vote(NSID(id))

            if not vote:
                await ctx.send_response(embed = embeds.fail("Vote introuvable."), ephemeral = True)
                return

            if not author:
                author = entities.create_user(NSID(ctx.author.id), ctx.author.display_name)

            if not author.position.permissions.manage_elections:
                await ctx.send_response(embed = embeds.fail("Vous n'avez pas la permission de gérer les élections."), ephemeral = True)
                return

            if vote.type == 'partial':
                candidates = sorted(vote.options.items(), key = lambda o: o[1].count, reverse = True)
                total = sum([ opt.count for id, opt in vote.options.items() if id != nsa.NSID(0x0) ]) # On exclut le vote blanc

                MAX_WINNERS = 3 # Pour l'instant on n'est même pas 10 sur le serveur donc bon

                if len(candidates) > MAX_WINNERS - 1:
                    winners = candidates[:MAX_WINNERS - 1]
                else:
                    winners = candidates

                position = entities.get_position('repr')
                role = ctx.guild.get_role(position.role)

                if not role:
                    await ctx.send_response(embed = embeds.fail(f"Impossible de trouver le rôle {position.role}."))
                    return

                await ctx.send_response(embed = embeds.votes.electionProposalsEmbed(vote))

                for c, w in winners:
                    c = NSID(c)

                    if c == nsa.NSID(0x0):
                        continue

                    user = entities.get_user(c)
                    candidate = state.get_candidate(c)
                    group = state.get_group(candidate.party.id)
                    d_user: discord.Member = await ctx.guild.fetch_member(int(c, 16))

                    if not user or not candidate or not d_user:
                        await ctx.send_followup(embed = embeds.fail(f"Impossible de trouver le candidat {c}."))
                        continue


                    user.set_position(position)
                    d_user.add_roles(role, f"Élection législative n°{vote.id}")

                    await ctx.send_followup(embed = embeds.elections.candidateInfoEmbed(
                        candidate = candidate,
                        user = user,
                        profile = d_user,
                        group = group
                    ))

                    candidate.current = None

                    if 'repr' in candidate.history.keys():
                        candidate.history['repr'] += 1
                    else:
                        candidate.history['repr'] = 1

                    candidate.save()

            elif vote.type == 'full':
                candidates = sorted(vote.options.items(), key = lambda o: o[1].count, reverse = True)
                total = sum([ opt.count for id, opt in vote.options.items() if id != nsa.NSID(0x0) ]) # On exclut le vote blanc

                c, w = candidates[1] if candidates[0][0] == nsa.NSID(0x0) else candidates[0] # On prend le gagnant en évitant le vote blanc
                c = NSID(c)

                position = entities.get_position('president_rep')
                role = ctx.guild.get_role(position.role)

                if not role:
                    await ctx.send_response(embed = embeds.fail(f"Impossible de trouver le rôle {position.role}."))
                    return

                await ctx.send_response(embed = embeds.votes.electionProposalsEmbed(vote))


                user = entities.get_user(c)
                candidate = state.get_candidate(c)
                group = state.get_group(candidate.party.id)
                d_user: discord.Member = await ctx.guild.fetch_member(int(c, 16))

                if not user or not candidate or not d_user:
                    await ctx.send_followup(embed = embeds.fail(f"Impossible de trouver le candidat {c}."))
                    return


                user.set_position(position)
                d_user.add_roles(role, f"Élection législative n°{vote.id}")

                await ctx.send_followup(embed = embeds.elections.candidateInfoEmbed(
                    candidate = candidate,
                    user = user,
                    profile = d_user,
                    group = group
                ))

                candidate.current = None

                if 'president_rep' in candidate.history.keys():
                    candidate.history['president_rep'] += 1
                else:
                    candidate.history['president_rep'] = 1

                candidate.save()

            else:
                await ctx.send_followup(embed = embeds.votes.voteProposalsEmbed(vote))
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)


def setup(bot):
    bot.add_cog(VotesCog(bot))