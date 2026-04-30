import discord
from discord import ui

class AddSubCategoryBtn(ui.Button):
    def __init__(self, bot, category_id, label="新增標籤", emoji="🏷️", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal import AddSubCategoryModal
        
        await interaction.response.send_modal(AddSubCategoryModal(self.bot, self.category_id))