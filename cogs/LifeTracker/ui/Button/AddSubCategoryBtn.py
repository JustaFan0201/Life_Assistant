import discord
from discord import ui

class AddSubCategoryBtn(ui.Button):
    def __init__(self, bot, category_id):
        super().__init__(label="新增子分類", style=discord.ButtonStyle.primary, emoji="🏷️", row=1)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal import AddSubCategoryModal
        
        await interaction.response.send_modal(AddSubCategoryModal(self.bot, self.category_id))