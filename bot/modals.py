import discord
from nsarchive import *
from bot.cogs.party_functions import party_functions
import bot.settings as settings

class CreatePartyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Creation de parti")
        
        self.add_item(discord.ui.InputText(label="Le nom de votre parti", max_length=32))
        self.add_item(discord.ui.InputText(label="Votre texte de promotion (facultatif)", placeholder="Ecrivez vos idées, votre programme, les bonnes raisons de rejoindre votre parti...", style=discord.InputTextStyle.long, required=False, max_length=1000))

    async def callback(self, interaction: discord.Interaction):
        
        name = self.children[0].value
        promotion_text = self.children[1].value
        
        if name.lower() in party_functions.get_parties_names(lower=True):
            return await interaction.response.send_message(embed=discord.Embed(title=f":x: Un parti possède déjà ce nom !", color = settings.bot_color), ephemeral=True)
        else:
            await interaction.response.send_message(embed=discord.Embed(title=f":white_check_mark: {name} a bien été crée !", color = settings.bot_color), ephemeral=True)
            await party_functions.create_party(name, promotion_text, interaction.user)

class RenameModal(discord.ui.Modal):
    def __init__(self, party: Organization):
        super().__init__(title="Renommer le parti")
        
        self.add_item(discord.ui.InputText(label="Entrez le nouveau nom", max_length=32))
        self.party = party

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value
        
        if self.party.name.lower() == name.lower():
            return await interaction.response.send_message(embed=discord.Embed(title=f":x: Votre parti possède déjà ce nom !", color = settings.bot_color), ephemeral=True)
             
        if name.lower() in party_functions.get_parties_names(lower=True):
            return await interaction.response.send_message(embed=discord.Embed(title=f":x: Un parti possède déjà ce nom !", color = settings.bot_color), ephemeral=True)
        else:
            await party_functions.rename(interaction, self.party, name)