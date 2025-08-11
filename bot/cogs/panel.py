import discord
from discord.ext import commands

import nsarchive as nsa
from nsarchive.models.base import NSID

from bot import embeds
from bot.views import parties as pw, panel as dw
from bot.utils import entities, state


def get_parties_names(lower: bool = False, exclude: str = None) -> list:
    parties: list[nsa.Organization] = entities.fetch_entities(position = 'parti')

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
        await ctx.defer(ephemeral = True)

        user = entities.get_entity(NSID(ctx.author.id))

        for grp in user.get_groups():
            if grp.position.id == 'parti':
                group: nsa.Organization = grp
                break
        else:
            group = None

        if group:
            party = state.get_party(group.id)
        else:
            party = None

        await ctx.send_followup(embed = embeds.elections.panelEmbed(user, group, party), view = dw.PanelView(group, party))


    @party_cmds.command(name = 'create')
    async def create_party(self, ctx: discord.ApplicationContext):
        author = entities.get_entity(ctx.author.id)

        if not author.position.permissions.organizations.append:
            await ctx.send_response(embed = embeds.res.failEmbed("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
            return

        modal = pw.NewPartyModal()
        await ctx.send_modal(modal)

    @party_cmds.command(name = 'join')
    async def join_party(self, ctx: discord.ApplicationContext, id: str):
        await ctx.defer(ephemeral = True)

        user = entities.get_entity(NSID(ctx.author.id))
        party = entities.get_entity(NSID(id))

        if not (party and party.position.id == 'parti'):
            await ctx.followup.send(embed = embeds.fail(f"L'ID `{party.id}` ne correspond à aucun parti."))
            return

        _groups = user.get_groups()

        for org in _groups:
            if org.position.id == "parti":
                if org.name == party.name:
                    await ctx.send_followup(embed = embeds.parties.alreadyInPartyEmbed(), ephemeral = True)   
                else:
                    await ctx.send_followup(embed = embeds.parties.inAnotherPartyEmbed(), ephemeral = True)

                return


        party_role = ctx.guild.get_role(party.additional['role'])

        await ctx.author.add_roles(party_role)


        party.add_member(user.id)

        party_channel = ctx.guild.get_channel(party.additional["channel"])

        for thread in party_channel.threads:
            if thread.name == "Activité":
                await thread.send(embed = embeds.parties.memberJoinedEmbed(ctx.author, party), content = ctx.author.mention)
        else:
            print(f"Impossible de retrouver le thread info de {party.name}")

        await ctx.send_followup(embed = embeds.success(), ephemeral = True)


def setup(bot):
    bot.add_cog(PartyCog(bot))