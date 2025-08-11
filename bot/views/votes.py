import random
import time

import discord
from discord import ui

import nsarchive as nsa
from nsarchive.models.base import *
from nsarchive import mandate

from bot import embeds
from bot.utils import entities, state, get_ts, get_dt

class OpenVoteModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title = "Ouvrir un vote")

        self.vote_title = discord.ui.InputText(
            style = discord.InputTextStyle.short,
            label = "Titre du vote",
            placeholder = "Les volcans, pour ou contre ?",
            required = True,
            max_length = 64
        )

        self.vote_start = discord.ui.InputText(
            style = discord.InputTextStyle.long,
            label = "Début du vote",
            placeholder = "AAAA-MM-JJ",
            required = False,
            min_length = 10,
            max_length = 10
        )

        self.vote_duration = discord.ui.InputText(
            style = discord.InputTextStyle.long,
            label = "Durée du vote",
            placeholder = "7d",
            required = False,
            max_length = 3
        )

        self.vote_options = discord.ui.InputText(
            style = discord.InputTextStyle.long,
            label = "Options",
            placeholder = "Séparez-les par des sauts de ligne",
            required = False
        )

        self.add_item(self.vote_title)
        self.add_item(self.vote_start)
        self.add_item(self.vote_duration)
        self.add_item(self.vote_options)

    async def callback(self, itx: discord.Interaction):
        await itx.response.defer()

        user = entities.get_entity(NSID(itx.user.id))

        _opts = self.vote_options.value.split("\n")
        _start = self.vote_start.value

        options = { nsa.NSID(random.randint(0x100000, 0xFFFFFF)): _opt for _opt in _opts }

        if _start == "now":
            start = round(time.time()) + 60
        else:
            start = get_ts(_start)

        if start - round(time.time()) > get_dt('2mo'):
            await itx.followup.send(embed = embeds.fail("Vous ne pouvez pas planifier un vote au-delà de 2 mois en avance."), ephemeral = True)
            return
        elif start < round(time.time()):
            await itx.followup.send(embed = embeds.fail("La date du vote est inférieure à la date actuelle."), ephemeral = True)
            return

        try:
            _d = get_dt(self.vote_duration.value)
            end = start + _d

            if _d > get_dt('2mo'):
                await itx.followup.send(embed = embeds.fail("La durée d'un vote ne peut pas dépasser 60 jours."), ephemeral = True)
                return
        except ValueError:
            await itx.followup.send(embed = embeds.fail("La durée donnée n'est pas valide."), ephemeral = True)
            return

        vote = state.alias(user.id).open_vote(
            title = self.vote_title.value,
            options = options,
            start = start,
            end = end
        )

        await itx.followup.send(embed = embeds.votes.voteProposalsEmbed(vote))

class ManageVoteView(ui.View):
    class AddVoteSelect(discord.ui.Select):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                placeholder = "Choisissez une option",
                options = [ discord.SelectOption(value = _id, label = opt.title) for _id, opt in vote.options.items() ]
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = True)
            user = entities.get_entity(NSID(itx.user.id))

            vote = state.alias(user.id).get_vote(self.vote.id)
            vote.add_vote(self.values[0])

            opt = vote.get(self.values[0])

            await itx.followup.send(embed = embeds.votes.voteSubmittedEmbed(vote, opt), ephemeral = True)

    class CloseVoteButton(discord.ui.Button):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                style = discord.ButtonStyle.red,
                label = "Clore",
                row = 2
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = False)
            user = entities.get_entity(NSID(itx.user.id))

            vote = state.alias(user.id).get_vote(self.vote.id)
            vote.close()

            await itx.followup.send(embed = embeds.success(), ephemeral = True)


    class ConvertToElectionButton(discord.ui.Button):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                style = discord.ButtonStyle.gray,
                label = "Convertir en élection",
                row = 2
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.send_message(embed = embeds.elections.elTypePresentationEmbed(), view = ManageElectionView(self.vote), ephemeral = True)

    def __init__(self, vote: nsa.Vote, author: nsa.User):
        super().__init__(timeout = 120, disable_on_timeout = True)

        if vote.endDate <= round(time.time()):
            return

        if len(vote.options) > 0:
            self.add_item(self.AddVoteSelect(vote))

        __close_button_added: bool = False

        if NSID(vote.author) == NSID(author.id):
            self.add_item(self.CloseVoteButton(vote))
            __close_button_added = True

        if author.position.permissions.candidacies.manage:
            try:
                election = state.get_election(vote.id)
            except:
                election = None

            if not election:
                self.add_item(self.ConvertToElectionButton(vote))

            if not __close_button_added:
                self.add_item(self.CloseVoteButton(vote))

class ManageElectionView(discord.ui.View):
    class ChooseElectionSelect(discord.ui.Select):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                placeholder = "Choissez un type d'élection",
                options = [
                    discord.SelectOption(value = "full", label = "Élections présidentielles"),
                    discord.SelectOption(value = "partial", label = "Élections législatives")
                ]
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = True)
            user = entities.get_entity(NSID(itx.user.id))
            vote = self.vote

            election = state.alias(user.id).open_election(
                vote,
                start = vote.startDate,
                full = self.values[0] == "full"
            )

            await itx.followup.send(embed = embeds.success(), ephemeral = True)
            await itx.channel.send(embed = embeds.elections.elPlannedEmbed(election, vote))

    def __init__(self, vote: nsa.Vote):
        super().__init__(timeout = 120, disable_on_timeout = True)

        self.add_item(self.ChooseElectionSelect(vote))

        self.vote = vote
