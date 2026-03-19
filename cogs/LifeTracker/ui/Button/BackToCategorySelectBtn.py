import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class BackToCategorySelectBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(label="返回", style=discord.ButtonStyle.danger, row=1)
        self.bot = bot
        
    async def callback(self, interaction: discord.Interaction):
        categories = LifeTrackerDatabaseManager.get_user_categories(interaction.user.id)
        
        from cogs.LifeTracker.ui.View import CategorySelectView
        
        embed, view = CategorySelectView.create_ui(self.bot, categories)
        await interaction.response.edit_message(embed=embed, view=view)