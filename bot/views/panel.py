import discord
from discord import ui

import nsarchive as nsa
from nsarchive.models.base import *
from nsarchive import mandate

from bot import embeds, settings
from bot.utils import entities, state

class SubmitCandidacyModal(discord.ui.Modal):
    def __init__(self, candidate: nsa.Candidate, election: nsa.Vote = None):
        super().__init__(title = "Candidater aux élections")

        self.candidate = candidate

        self.election = discord.ui.InputText(
            style = discord.InputTextStyle.short,
            label = "ID de l'élection",
            placeholder = "NSID fourni par un Sage ou un bot (entre 10 et 12 chiffres)",
            required = True,
            min_length = 10,
            max_length = 12,
            value = election.id if election else None
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

        user = entities.get_user(NSID(itx.user.id))
        candidate = self.candidate

        if candidate:
            party = candidate.party
        else:
            party = None

        if not party:
            await itx.followup.send("Vous devez être membre d'un parti pour vous présenter.")
            return

        group = entities.get_group(candidate.party.id)

        # Modification du vote
        vote = state.get_vote(self.election.value)
        vote.options[user.id] = nsa.VoteOption(f"{user.name} ({group.name})")
        vote.save()

        # Update du profil de candidature
        candidate.current = vote.id
        candidate.save()

        channel = itx.guild.get_channel(settings.CHANNELS['party_echo'])

        await itx.followup.send(embed = embeds.elections.candidacySubmittedEmbed(party), ephemeral = True)
        await channel.send(embed = embeds.elections.newCandidateEmbed(
            vote,
            entities.get_group(party.id),
            user = user,
            candidate = candidate,
            profile = itx.user,
            speech = self.discours.value
        ))

class PanelView(ui.View):
    class SubmitCandidacyButton(discord.ui.Button):
        def __init__(self, candidate: nsa.Candidate = None):
            super().__init__(
                style = discord.ButtonStyle.green,
                label = "Se présenter",
                disabled = mandate.get_phase() not in ('paix', 'undefined') or not candidate
            )

            self.candidate = candidate

        async def callback(self, itx: discord.Interaction):
            cycle = mandate.get_cycle()
            phase = mandate.get_phase()

            user = entities.get_user(NSID(itx.user.id))
            candidate = self.candidate

            if not (user and user.position.permissions.citizen):
                await itx.followup.send("Vous ne détenez pas la citoyenneté et ne pouvez donc pas vous présenter.")
                return

            if not candidate.party:
                await itx.followup.send("Vous devez être membre d'un parti pour vous présenter.")
                return

            if phase not in ('paix', 'undefined'):
                await itx.response.send_message("Vous ne pouvez pas candidater pendant les élections.")
                return

            await itx.response.send_modal(SubmitCandidacyModal(candidate))

    def __init__(self, group: nsa.Organization = None, candidate: nsa.Candidate = None):
        super().__init__(timeout = 300)

        if candidate and candidate.party:
            self.add_item(self.SubmitCandidacyButton(candidate))

        self.group = group
        self.candidate = candidate