import discord
from discord import ui
from ..Modal.ContactModals import AddEmailListModal

class AddContactBtn(ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="添加聯絡人", style=discord.ButtonStyle.primary, emoji="➕")
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddEmailListModal(self.cog, self.user_id))