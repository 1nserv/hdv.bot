import discord
from discord import ui

import nsarchive as nsa
from nsarchive.models.base import *
from nsarchive import mandate

from bot import embeds, settings
from bot.utils import entities, state

class SubmitCandidacyModal(discord.ui.Modal):
    def __init__(self, party: nsa.Party):
        super().__init__(title = "Candidater aux élections")

        self.party = party

        self.election = discord.ui.InputText(
            style = discord.InputTextStyle.short,
            label = "ID de l'élection",
            placeholder = "NSID fourni par un Sage ou un bot",
            required = True,
            min_length = 4,
            max_length = 16
        )

        self.discours = discord.ui.InputText(
            style = discord.InputTextStyle.long,
            label = "Profession de foi",
            placeholder = "Discours de promotion, programme, pas d'insultes...",
            required = False,
            max_length = 1024
        )

        self.add_item(self.election)
        self.add_item(self.discours)

    async def callback(self, itx: discord.Interaction):
        await itx.response.defer()

        user = entities.get_entity(NSID(itx.user.id))
        party = self.party

        election = state.alias(user.id).get_election(self.election.value)

        election.submit_candidacy()

        await itx.followup.send("T'es retenu khoya")

class SubmitPartyModal(discord.ui.Modal):
    def __init__(self, group: nsa.Organization):
        super().__init__(title = f"Enregistrement du parti {group.name}")

        self.group = group

        self.color = discord.ui.InputText(
            style = discord.InputTextStyle.short,
            label = "Couleur",
            placeholder = "#123ABC",
            required = True,
            min_length = 7,
            max_length = 7
        )

        self.motto = discord.ui.InputText(
            style = discord.InputTextStyle.singleline,
            label = "Devise du parti",
            placeholder = "L'onion fait l'afro",
            required = False,
            max_length = 64
        )

        self.prom = discord.ui.InputText(
            style = discord.InputTextStyle.paragraph,
            label = "Discours de promotion",
            placeholder = "#123ABC",
            required = False,
            max_length = 1024
        )

        self.add_item(self.color)
        self.add_item(self.motto)
        self.add_item(self.prom)

    async def callback(self, itx: discord.Interaction):
        await itx.response.defer()

        user = entities.get_entity(itx.user.id)
        grp = self.group

        if len(grp.members) + 1 < 1:
            await itx.followup.send(f"Vous n'avez pas assez de membres pour enregistrer un parti ({len(grp.members) + 1}/2 members requis)")
            return

        try:
            _color = int(self.color.value[1:], 16)
        except:
            await itx.followup.send(f"La couleur `{self.color.value}` n'est pas au format hexadécimal.")
            return


        party = state.alias(user.id).register_party(
            id = grp.id,
            color = _color,
            motto = self.motto.value
        )


        # Création du rôle du parti

        role = await itx.guild.create_role(
            name = grp.name,
            hoist = True,
            mentionable = False,
            color = _color
        )

        grp.add_link('role', role.id)


        # Création du forum

        __party_cgr = itx.guild.get_channel(settings.CATEGORIES['parties'])

        channel = await __party_cgr.create_forum_channel(
            name = grp.name,
            position = 2
        )

        overwrite = {
            itx.guild.default_role: discord.PermissionOverwrite(view_channel = False, send_messages = False),
            role: discord.PermissionOverwrite(view_channel = True, send_messages = True)
        }

        for role, perms in overwrite.items():
            await channel.set_permissions(role, overwrite = perms)

        grp.add_link('channel', channel.id)


        await channel.create_thread(
            name = "Général",
            content = role.mention,
            embed = embeds.parties.welcomeEmbed(grp)
        )

        th_infos = await channel.create_thread(
            name = "Informations",
            content = role.mention,
            embed = embeds.parties.partyCreatedEmbed(grp)
        )

        await th_infos.edit(pinned = True, locked = True)

        grp.add_link('info_thread', th_infos.id)


        # Annonce de la nouvelle

        __echo__channel = await itx.guild.get_channel(settings.CHANNELS['party_echo'])
        await __echo__channel.send(embed = embeds.parties.partyCreated_LOG(grp, self.prom.value))


        await itx.followup.send(embed = embeds.elections.panelEmbed(user, grp, party))

class PanelView(ui.View):
    class SubmitCandidacyButton(discord.ui.Button):
        def __init__(self, party: nsa.Party = None):
            super().__init__(
                style = discord.ButtonStyle.green,
                label = "Se présenter",
                disabled = mandate.get_phase() not in ('paix', 'undefined') or not party
            )

            self.party = party

        async def callback(self, itx: discord.Interaction):
            cycle = mandate.get_cycle()
            phase = mandate.get_phase()

            user = entities.get_entity(NSID(itx.user.id))
            party = self.party

            if not (user and user.position.permissions.candidacies.append):
                await itx.followup.send("Vous ne détenez pas la citoyenneté et ne pouvez donc pas vous présenter.")
                return

            if not party:
                await itx.followup.send("Votre parti existe mais n'est pas confirmé.")
                return

            if phase not in ('paix', 'undefined'):
                await itx.response.send_message("Vous ne pouvez pas candidater pendant les élections.")
                return

            await itx.response.send_modal(SubmitCandidacyModal(party))

    class SubmitPartyButton(discord.ui.Button):
        def __init__(self, group: nsa.Organization = None):
            super().__init__(
                style = discord.ButtonStyle.gray,
                label = "Enregistrer son parti"
            )

            self.group = group

        async def callback(self, itx: discord.Interaction):
            await itx.response.send_modal(SubmitPartyModal(self.group))

    def __init__(self, group: nsa.Organization = None, party: nsa.Party = None):
        super().__init__(timeout = 300)

        if party:
            self.add_item(self.SubmitCandidacyButton(party))
        elif group:
            self.add_item(self.SubmitPartyButton(group))

        self.group = group
        self.party = party