import discord
from discord import ui

import nsarchive as nsa
from nsarchive.models.base import *
from nsarchive import mandate

from bot import embeds, settings
from bot.utils import entities, state, warn
from bot.views import parties as pw


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

        channel = itx.guild.get_channel(settings.CHANNELS['election_echo'])

        await itx.followup.send(embed = embeds.elections.candidacySubmittedEmbed(party), ephemeral = True)
        await channel.send(embed = embeds.elections.newCandidateEmbed(
            vote,
            entities.get_group(party.id),
            user = user,
            candidate = candidate,
            profile = itx.user,
            speech = self.discours.value
        ))



class SelectPartyView(discord.ui.View):
    class PartySelect(discord.ui.Select):
        def __init__(self):
            super().__init__(placeholder = "Choisissez un parti", options = [])

            self.add_option(label = "Créer mon parti", value = "create", emoji = "\u2795")

            parties = entities.fetch_groups(position = 'parti')

            for grp in parties:
                self.add_option(label = grp.name, value = str(grp.id))

        async def callback(self, itx: discord.Interaction):
            if self.values[0] == "create":
                await itx.response.send_modal(pw.NewPartyModal())
            else:
                party = state.get_party(NSID(self.values[0]))

                user = entities.get_user(NSID(itx.user.id))
                candidate = state.get_candidate(NSID(itx.user.id))
                party = state.get_party(NSID(self.values[0]))
                group = entities.get_group(party.id)

                if not party:
                    await itx.response.send(embed = embeds.fail("Le parti spécifié n'existe pas."), ephemeral = True)
                    return

                if not user:
                    user = entities.create_user(NSID(itx.user.id), itx.user.display_name)

                if not user.position.permissions.citizen:
                    await itx.response.send(embed = embeds.fail("Vous devez être un citoyen."), ephemeral = True)
                    return

                if not candidate:
                    candidate = state.add_candidate(user.id)

                _org = candidate.party
                if _org:
                    if _org.id == party.id:
                        await itx.response.send(embed = embeds.parties.alreadyInPartyEmbed(), ephemeral = True)   
                    else:
                        await itx.response.send(embed = embeds.parties.inAnotherPartyEmbed(), ephemeral = True)

                    return
                else:
                    group.add_member(user.id)
                    candidate.party = party.id
                    candidate.save()


                party_role = itx.guild.get_role(party.additional['role'])
                await itx.user.add_roles(party_role)

                party_channel = itx.guild.get_channel(party.additional['channel'])

                for thread in party_channel.threads:
                    if thread.name == "Informations":
                        await thread.send(embed = embeds.parties.memberJoinedEmbed(itx.user, party), content = itx.user.mention)
                        break
                else:
                    warn(f"Impossible de retrouver le thread info de {party.name}")

                await itx.response.send(embed = embeds.success(), ephemeral = True)

    def __init__(self):
        super().__init__(timeout = 120, disable_on_timeout = True)

        self.add_item(self.PartySelect())

class PanelView(ui.View):
    class SubmitCandidacyButton(discord.ui.Button):
        def __init__(self, candidate: nsa.Candidate = None):
            super().__init__(
                style = discord.ButtonStyle.green,
                label = "Candidater",
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

    class JoinPartyButton(discord.ui.Button):
        def __init__(self):
            super().__init__(
                style = discord.ButtonStyle.blurple,
                label = "Rejoindre un parti"
            )

        async def callback(self, itx: discord.Interaction):
            _groups = entities.fetch_groups(position = 'parti')
            await itx.response.send(embed = embeds.parties.partyListEmbed(_groups), view = SelectPartyView(), ephemeral = True)

    class LeavePartyButton(discord.ui.Button):
        def __init__(self):
            super().__init__(
                style = discord.ButtonStyle.red,
                label = "Quitter mon parti"
            )

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral = True)
            user = entities.get_user(itx.user.id)
            candidate = state.get_candidate(user.id)
            party = candidate.party

            if not party:
                await itx.followup.send(embed = embeds.parties.notInAnyPartyEmbed(), ephemeral = True)
                return

            group = entities.get_group(party.id)

            _transmission: bool = False

            if group.owner.id == user.id:
                for _member_id, _member in group.members.items():
                    if _member.manager:
                        group.set_owner(entities.get_user(_member_id))

                        _transmission = True
                else:
                    await itx.followup.send(embed = embeds.fail("Accordez le grade Gérant à l'un des membres du parti pour qu'il en devienne automatiquement président à votre départ. Vous pouvez le faire via `/party promote_member`."))
                    return
            else:
                group.remove_member(group.members[user.id])

            candidate.party = None
            candidate.save()

            party_role = itx.guild.get_role(group.additional['role'])
            await itx.user.remove_roles(party_role)

            party_channel = itx.guild.get_channel(group.additional['channel'])

            for thread in party_channel.threads:
                if thread.name == "Informations":
                    if _transmission:
                        await thread.send(embed = embeds.parties.partyTransmittedEmbed(group), content = itx.user.mention)
                    else:
                        await thread.send(embed = embeds.parties.memberLeftEmbed(itx.user, group), content = itx.user.mention)
            else:
                warn(f"Impossible de retrouver le thread info de {group.name}")

            await itx.followup.send(embed = embeds.success(), ephemeral = True)

    def __init__(self, user: nsa.User):
        super().__init__(timeout = 300)

        candidate = state.get_candidate(user.id)

        if not candidate:
            candidate = state.add_candidate(user.id)

        if candidate.party:
            self.add_item(self.SubmitCandidacyButton(candidate))
            self.add_item(self.LeavePartyButton())
        else:
            self.add_item(self.JoinPartyButton())