import time

import discord

import nsarchive as nsa

from bot import embeds
from bot.utils import entities


class NewPartyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title = "Créer un parti")
        self.name = discord.ui.InputText(label = "Nom du parti", placeholder = "Entrez un nom ici...", max_length = 32, required = True)

        self.add_item(self.name)

    async def callback(self, itx: discord.Interaction):
        await itx.response.defer()

        owner = entities.get_entity(nsa.NSID(itx.user.id))

        if owner is None:
            await itx.followup.send(embed = embeds.res.failEmbed("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
            return

        if not owner.position.permissions.organizations.append:
            await itx.followup.send(embed = embeds.res.failEmbed("Vous n'avez pas la permission de créer un parti."), ephemeral = True)
            return

        _id = nsa.NSID(itx.user.id // round(time.time()))

        org = entities.alias(owner.id).create_entity(_id, self.name.value, 'organization', 'parti')

        await itx.followup.send(f"Votre parti est créé sous l'identifiant `{org.id}`. Faites `/panel` ou `/group info` pour le voir.", delete_after = 60)