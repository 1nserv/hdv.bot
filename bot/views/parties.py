import time

import discord

import nsarchive as nsa
from nsarchive.models.base import NSID

from bot import embeds, settings
from bot.utils import entities, state, warn


class NewPartyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title = "Créer un parti")

        self.name = discord.ui.InputText(
            label = "Nom du parti",
            placeholder = "Entrez un nom ici...",
            max_length = 32,
            required = True
        )

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
            placeholder = "Faites la promo de votre parti",
            required = False,
            max_length = 1024
        )

        self.add_item(self.name)
        self.add_item(self.color)
        self.add_item(self.motto)
        self.add_item(self.prom)

    async def callback(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral = True)
        user = entities.get_user(nsa.NSID(itx.user.id))

        if user is None:
            await itx.followup.send(embed = embeds.res.failEmbed("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
            return

        if not user.position.permissions.create_groups:
            await itx.followup.send(embed = embeds.res.failEmbed("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
            return


        # Création du groupe associé

        _id = nsa.NSID(round(time.time() * 1000))
        grp = entities.create_group(_id, self.name.value, 'parti')
        grp.set_owner(user)


        # Création du parti

        try:
            _color = int(self.color.value[1:], 16)
        except:
            await itx.followup.send(embed = embeds.fail(f"La couleur `{self.color.value}` n'est pas au format hexadécimal."))
            return

        party = state.register_party(
            id = grp.id,
            color = _color,
            motto = self.motto.value
        )


        # Update du profil candidat

        candidate = state.get_candidate(user.id)

        if candidate:
            candidate.party = party
            candidate.save()
        else:
            candidate = state.add_candidate(user.id, party)


        # Création du rôle du parti

        role = await itx.guild.create_role(
            name = grp.name,
            hoist = True,
            mentionable = False,
            color = _color
        )

        __sep_role: discord.Role = itx.guild.get_role(settings.ROLES['party_sep'])

        await role.edit(position = __sep_role.position)

        await itx.user.add_roles(role)

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

        __echo__channel = itx.guild.get_channel(settings.CHANNELS['party_echo'])
        await __echo__channel.send(embed = embeds.parties.partyCreated_LOG(grp, self.prom.value))

        await itx.followup.send(embed = embeds.success(), ephemeral = True)


class JoinRequestView(discord.ui.View):
    class AcceptRequestButton(discord.ui.Button):
        def __init__(self, member: discord.Member, party: nsa.Organization):
            super().__init__(label = "Accepter", style = discord.ButtonStyle.green)
            self.member = member
            self.party = party

        async def callback(self, itx: discord.Interaction):
            await itx.response.defer()

            # On actualise chaque objet au cas où des modifications aient été effectuées entre l'envoi et la réponse
            party = state.get_party(self.party.id)
            user = entities.get_user(self.member.id)
            author = entities.get_user(itx.user.id)
            candidate = state.get_candidate(user.id)
            group = entities.get_group(party.id)

            if not party:
                await itx.followup.send(embed = embeds.fail("Le parti spécifié n'existe plus."), ephemeral = True)
                return

            if not user:
                await itx.followup.send(embed = embeds.fail("L'utilisateur spécifié n'existe plus."), ephemeral = True)
                return

            if not author:
                # "Vous n'existez plus" ?
                author = entities.add_user(itx.user.id)

            if not candidate:
                candidate = state.add_candidate(user.id)

            if candidate.party:
                await itx.followup.send(embed = embeds.parties.inAnotherPartyEmbed(True), ephemeral = True)
                return

            _auth = group.members.get(author.id)

            if not (_auth and (_auth.manager or _auth.level > 1)):
                await itx.followup.send(embed = embeds.fail("Vous n'avez plus la permission d'accepter des membres dans ce parti."), ephemeral = True)
                return

            group.add_member(user.id)
            candidate.party = party
            candidate.save()


            party_role = itx.guild.get_role(party.additional['role'])
            await self.member.add_roles(party_role)

            party_channel = itx.guild.get_channel(party.additional['channel'])

            for thread in party_channel.threads:
                if thread.name == "Informations":
                    await thread.send(embed = embeds.parties.memberJoinedEmbed(self.member, party), content = self.member.mention)
                    break
            else:
                warn(f"Impossible de retrouver le thread info de {party.name}")

            await itx.response.send_message(embed = embeds.success(), ephemeral = True)

            self.party.add_member(self.member.id)
            await itx.followup.send(embed = embeds.success(), ephemeral = True)

    def __init__(self, member: discord.Member, party: nsa.Organization):
        super().__init__(timeout = 86400, disable_on_timeout = True)
        self.member = member
        self.party = party

        self.add_item(self.AcceptRequestButton(member, party))