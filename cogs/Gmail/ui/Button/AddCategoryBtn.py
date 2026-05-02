import discord
from discord import ui
from cogs.Gmail.ui.Modal.AddCategoryModal import AddCategoryModal
class AddCategoryBtn(ui.Button):
    def __init__(self, gmail_cog, user_id, row=2):
        super().__init__(label="新增分類", style=discord.ButtonStyle.success, emoji="🏷️", row=1)
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddCategoryModal(self.gmail_cog, self.user_id))