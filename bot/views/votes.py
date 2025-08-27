import random
import time

import discord
from discord import ui

import nsarchive as nsa
from nsarchive.models.base import *
from nsarchive import mandate

from bot import embeds
from bot.utils import entities, state, get_ts, get_dt
from bot.views import panel


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
            style = discord.InputTextStyle.singleline,
            label = "Début du vote",
            placeholder = "AAAA-MM-JJ",
            required = False,
            min_length = 10,
            max_length = 10
        )

        self.vote_duration = discord.ui.InputText(
            style = discord.InputTextStyle.singleline,
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

        user = entities.get_user(NSID(itx.user.id))

        _opts = self.vote_options.value.split("\n")
        _start = self.vote_start.value

        options = _opts

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

        vote = state.open_vote(
            title = self.vote_title.value,
            author = user.id,
            options = options,
            start = start,
            end = end
        )

        await itx.followup.send(embed = embeds.votes.voteProposalsEmbed(vote))

class ManageVoteView(ui.View):
    class AddVoteSelect(discord.ui.Select):
        def __init__(self, vote: nsa.Vote):
            if vote.max_choices == 1:
                _p = "Choisissez une option"
            elif vote.min_choices == vote.max_choices:
                _p = f"Choisissez {vote.min_choices} options"
            elif vote.min_choices - vote.max_choices == 1:
                _p = f"Choisissez {'une' if vote.min_choices == 1 else vote.min_choices} ou {vote.max_choices} options"
            else:
                _p = f"Choisissez entre {'une' if vote.min_choices == 1 else vote.min_choices} et {vote.max_choices} options"

            super().__init__(
                placeholder = _p,
                options = [ discord.SelectOption(value = _id, label = opt.title) for _id, opt in vote.options.items() ],
                max_values = vote.max_choices,
                min_values = vote.min_choices
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = True)
            user = entities.get_user(NSID(itx.user.id))

            vote = state.get_vote(self.vote.id)

            if "0" in self.values and len(self.values) > 1:
                await itx.followup.send(embed = embeds.fail("Vous ne pouvez pas voter blanc en même temps que d'autres options."), ephemeral = True)
                return

            vote.add_votes(user.id, *tuple(self.values))
            vote.save()

            opts = [ vote.get(v) for v in self.values ]

            await itx.followup.send(embed = embeds.votes.voteSubmittedEmbed(vote, opts), ephemeral = True)

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
            user = entities.get_user(NSID(itx.user.id))

            if not user.position.permissions.manage_votes:
                await itx.followup.send(embed = embeds.fail("Vous n'avez pas la permission de gérer les votes."), ephemeral = True)
                return

            vote = state.get_vote(self.vote.id)
            vote.close()

            await itx.followup.send(embed = embeds.success(), ephemeral = True)

    class ConvertButton(discord.ui.Button):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                style = discord.ButtonStyle.gray,
                label = "Convertir",
                row = 2
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.send_message(embed = embeds.elections.elTypePresentationEmbed(), view = ConvertVoteView(self.vote), ephemeral = True)


    class SubmitCandidacyButton(discord.ui.Button):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                style = discord.ButtonStyle.blurple,
                label = "Se présenter",
                row = 2
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            user = entities.get_user(NSID(itx.user.id))
            candidate = state.get_candidate(user.id)

            if not user.position.permissions.citizen:
                await itx.response.send(embed = embeds.fail("Vous n'avez pas la permission de vous présenter."), ephemeral = True)
                return

            if not candidate:
                candidate = state.create_candidate(user.id)

            if candidate.current:
                await itx.response.send(embed = embeds.fail("Vous êtes déjà candidat à une élection."), ephemeral = True)
                return

            if not candidate.party:
                await itx.response.send(embed = embeds.fail("Vous devez être membre d'un parti pour vous présenter."), ephemeral = True)
                return

            await itx.response.send_modal(panel.SubmitCandidacyModal(candidate, self.vote))

    class CancelCandidacyButton(discord.ui.Button):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                style = discord.ButtonStyle.red,
                label = "Annuler ma candidature",
                row = 2
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            user = entities.get_user(NSID(itx.user.id))
            candidate = state.get_candidate(user.id)

            if not candidate:
                await itx.response.send(embed = embeds.fail("Vous n'êtes pas candidat à une élection."), ephemeral = True)
                return

            if candidate.current != self.vote.id:
                await itx.response.send(embed = embeds.fail("Vous n'êtes pas candidat à cette élection."), ephemeral = True)
                return

            candidate.current = None
            candidate.save()

            self.vote.options.pop(str(candidate.id), None)
            self.vote.save()

            await itx.response.send(embed = embeds.success(), ephemeral = True)

    def __init__(self, vote: nsa.Vote, author: nsa.User = None):
        super().__init__(timeout = 120, disable_on_timeout = True)

        if vote.end_date <= round(time.time()):
            return

        if len(vote.options) > 1 and vote.start_date < round(time.time()):
            self.add_item(self.AddVoteSelect(vote))

        if not author:
            self.add_item(self.SubmitCandidacyButton(vote))
            return

        __close_button_added: bool = False

        if NSID(vote.author) == NSID(author.id):
            self.add_item(self.CloseVoteButton(vote))
            __close_button_added = True

        if author.position.permissions.manage_votes:
            if vote.type == 'normal':
                self.add_item(self.ConvertButton(vote))

            if not __close_button_added:
                self.add_item(self.CloseVoteButton(vote))

class ConvertVoteView(discord.ui.View):
    class ChooseTypeSelect(discord.ui.Select):
        def __init__(self, vote: nsa.Vote):
            super().__init__(
                placeholder = "Choisissez un type de vote",
                options = [
                    discord.SelectOption(value = "full", label = "Élections présidentielles"),
                    discord.SelectOption(value = "partial", label = "Élections législatives"),
                    discord.SelectOption(value = "2pos", label = "Vote pour ou contre"),
                    discord.SelectOption(value = "3pos", label = "Vote pour ou contre (avec vote blanc)"),
                ]
            )

            self.vote = vote

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = True)
            user = entities.get_user(NSID(itx.user.id))

            if not user.position.permissions.manage_votes:
                await itx.followup.send(embed = embeds.fail("Vous n'avez pas la permission de gérer les votes."), ephemeral = True)
                return

            vote = self.vote

            vote.type = self.values[0]

            if vote.type == 'full':
                vote.options = {
                    nsa.NSID(0x0): nsa.VoteOption("S'abstient")
                }

                vote.majority = 50

                vote.min_choices = 1
                vote.max_choices = 1

                vote.anonymous = True
                vote.voters = []

            elif vote.type == 'partial':
                vote.options = {
                    nsa.NSID(0x0): nsa.VoteOption("S'abstient")
                }

                vote.majority = 50

                vote.min_choices = 1
                vote.max_choices = 2

                vote.anonymous = True
                vote.voters = []

            elif vote.type == '2pos':
                vote.options = {
                    nsa.NSID(0x0): nsa.VoteOption("Pour"),
                    nsa.NSID(0x1): nsa.VoteOption("Contre")
                }

                vote.majority = 60

                vote.min_choices = 1
                vote.max_choices = 1

                vote.anonymous = False
                vote.voters = []

            elif vote.type == '3pos':
                vote.options = {
                    nsa.NSID(0x0): nsa.VoteOption("Pour"),
                    nsa.NSID(0x1): nsa.VoteOption("Contre"),
                    nsa.NSID(0x2): nsa.VoteOption("S'abstient")
                }

                vote.majority = 60

                vote.min_choices = 1
                vote.max_choices = 1

                vote.anonymous = False
                vote.voters = []

            vote.save()

            if vote.type in ('full', 'partial'):
                await itx.channel.send(embed = embeds.elections.elPlannedEmbed(vote))

            await itx.followup.send(embed = embeds.success(), ephemeral = True)

    def __init__(self, vote: nsa.Vote):
        super().__init__(timeout = 120, disable_on_timeout = True)

        self.add_item(self.ChooseTypeSelect(vote))

        self.vote = vote
