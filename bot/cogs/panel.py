import discord
from discord.ext import commands

import nsarchive as nsa
from nsarchive.models.base import NSID

from bot import embeds
from bot.views import parties as pw, panel as dw
from bot.utils import entities, state, log, warn, usererror, fatalerror


def get_parties_names(lower: bool = False, exclude: str = None) -> list:
    parties: list[nsa.Organization] = entities.fetch_groups(position = 'parti')

    if lower:
        if len(parties) != 1:
            return [ party.name.lower() for party in parties if party.name != exclude ]
        else:
            return [ party.name.lower() for party in parties ]
    else:
        if len(parties) != 1:
            return [ party.name for party in parties if party.name != exclude ]
        else:
            return [ party.name for party in parties ]


class PartyCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    party_cmds = discord.SlashCommandGroup(name = 'party')

    @commands.slash_command(name = 'panel')
    async def display_panel(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /panel")
        try:
            await ctx.defer(ephemeral = True)

            user = entities.get_user(NSID(ctx.author.id))

            if not user:
                user = entities.create_user(NSID(ctx.author.id), ctx.author.display_name)

            candidate = state.get_candidate(user.id)

            if not candidate:
                candidate = state.add_candidate(user.id)

            if candidate.party:
                group = entities.get_group(candidate.party.id)
            else:
                group = None


            await ctx.send_followup(embed = embeds.elections.panelEmbed(user, group, candidate), view = dw.PanelView(user))
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'list')
    async def list_parties(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /list")
        try:
            await ctx.defer()

            groups: list[nsa.Organization] = entities.fetch_groups(position = 'parti')

            await ctx.send_followup(embed = embeds.parties.partyListEmbed(groups), view = dw.SelectPartyView(), ephemeral = True)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'create')
    async def create_party(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /create")
        try:
            author = entities.get_user(ctx.author.id)

            if not author:
                author = entities.create_user(ctx.author.id, ctx.author.display_name)

            candidate = state.get_candidate(author.id)

            if not candidate:
                candidate = state.add_candidate(author.id)

            if candidate.party:
                await ctx.send_response(embed = embeds.fail("Vous êtes déjà membre d'un parti."), ephemeral = True)
                return

            if not author.position.permissions.create_parties:
                await ctx.send_response(embed = embeds.fail("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
                return

            modal = pw.NewPartyModal()
            await ctx.send_modal(modal)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'join')
    async def join_party(self, ctx: discord.ApplicationContext, id: str):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /join")
        try:
            await ctx.defer(ephemeral = True)

            user = entities.get_user(NSID(ctx.author.id))
            candidate = state.get_candidate(NSID(ctx.author.id))
            party = state.get_party(id)
            group = entities.get_group(party.id)

            if not party:
                await ctx.send_followup(embed = embeds.fail("Le parti spécifié n'existe pas."), ephemeral = True)
                return

            if not user:
                user = entities.create_user(NSID(ctx.author.id), ctx.author.display_name)

            if not user.position.permissions.citizen:
                await ctx.send_followup(embed = embeds.fail("L'utilisateur doit être un citoyen."), ephemeral = True)
                return

            if not candidate:
                candidate = state.add_candidate(user.id)

            _org = candidate.party

            if _org:
                if _org.id == party.id:
                    await ctx.send_followup(embed = embeds.parties.alreadyInPartyEmbed(True), ephemeral = True)   
                else:
                    await ctx.send_followup(embed = embeds.parties.inAnotherPartyEmbed(True), ephemeral = True)

                return
            else:
                group.add_member(user.id)
                candidate.party = party.id
                candidate.save()


            party_role = ctx.guild.get_role(party.additional['role'])
            await ctx.author.add_roles(party_role)

            party_channel = ctx.guild.get_channel(party.additional['channel'])

            for thread in party_channel.threads:
                if thread.name == "Informations":
                    await thread.send(embed = embeds.parties.memberJoinedEmbed(ctx.author, party), content = ctx.author.mention)
                    break
            else:
                warn(f"Impossible de retrouver le thread info de {party.name}")

            await ctx.send_followup(embed = embeds.success(), ephemeral = True)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'leave')
    async def leave_party(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /leave")
        try:
            await ctx.defer()
            user = entities.get_user(ctx.author.id)
            candidate = state.get_candidate(user.id)
            party = candidate.party

            if not party:
                await ctx.send_followup(embed = embeds.parties.notInAnyPartyEmbed())
                return

            group = entities.get_group(party.id)

            _transmission: bool = False

            if group.owner.id == user.id:
                for _member_id, _member in group.members.items():
                    if _member.manager:
                        group.set_owner(entities.get_user(_member_id))

                        _transmission = True
                else:
                    await ctx.send_followup(embed = embeds.fail("Accordez le grade Gérant à l'un des membres du parti pour qu'il en devienne automatiquement président à votre départ. Vous pouvez le faire via `/party promote_member`."))
                    return
            else:
                group.remove_member(group.members[user.id])

            candidate.party = None
            candidate.save()

            party_role = ctx.guild.get_role(group.additional['role'])
            await ctx.author.remove_roles(party_role)

            party_channel = ctx.guild.get_channel(group.additional['channel'])

            for thread in party_channel.threads:
                if thread.name == "Informations":
                    if _transmission:
                        await thread.send(embed = embeds.parties.partyTransmittedEmbed(group), content = ctx.author.mention)
                    else:
                        await thread.send(embed = embeds.parties.memberLeftEmbed(ctx.author, group), content = ctx.author.mention)
            else:
                warn(f"Impossible de retrouver le thread info de {group.name}")

            await ctx.send_followup(embed = embeds.success(), ephemeral = True)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'rename')
    async def rename_party(self, ctx: discord.ApplicationContext, name: str):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /rename")
        try:
            await ctx.defer()
            user = entities.get_user(ctx.author.id)
            candidate = state.get_candidate(user.id)

            if not (candidate and candidate.party):
                await ctx.send_followup(embed = embeds.parties.notInAnyPartyEmbed())
                return

            party = candidate.party

            if party:
                group = entities.get_group(party.id)
            else:
                await ctx.send_followup(embed = embeds.parties.notInAnyPartyEmbed())
                return

            if group.owner.id == user.id:
                group.set_name(name)
            elif group.members[user.id].manager:
                group.set_name(name)
            else:
                await ctx.send_followup(embed = embeds.fail("Vous n'avez pas la permission de renommer ce parti."))
                return


            party_channel = ctx.guild.get_channel(group.additional['channel'])

            for thread in party_channel.threads:
                if thread.name == "Informations":
                    await thread.send(embed = embeds.parties.partyRenamedEmbed(group), content = ctx.author.mention)
            else:
                warn(f"Impossible de retrouver le thread info de {group.name}")

            await ctx.send_followup(embed = embeds.success(), ephemeral = True)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)

    @party_cmds.command(name = 'delete')
    async def delete_party(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name} ({NSID(ctx.user.id)}) utilise /delete")
        try:
            await ctx.defer()
            user = entities.get_user(ctx.author.id)
            candidate = state.get_candidate(user.id)

            if not (candidate and candidate.party):
                await ctx.send_followup(embed = embeds.parties.notInAnyPartyEmbed())
                return

            party = candidate.party

            if party:
                group = entities.get_group(party.id)
            else:
                await ctx.send_followup(embed = embeds.parties.notInAnyPartyEmbed())
                return

            if group.owner.id == user.id:
                entities.delete_entity(group.id)
            else:
                await ctx.send_followup(embed = embeds.fail("Vous n'avez pas la permission de supprimer ce parti."))
                return


            party_role: discord.Role = ctx.guild.get_role(group.additional['role'])
            await party_role.delete()

            party_channel: discord.ForumChannel = ctx.guild.get_channel(group.additional['channel'])
            party_channel.delete()

            await ctx.send_followup(embed = embeds.success(), ephemeral = True)
        except Exception as e:
            await ctx.channel.send(embed = embeds.fail("Une erreur est survenue."))
            fatalerror(e)



def setup(bot):
    bot.add_cog(PartyCog(bot))