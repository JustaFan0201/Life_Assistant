import discord
from discord import ui

class BackToDetailBtn(ui.Button):
    def __init__(self, bot, category_id):
        super().__init__(label="返回", style=discord.ButtonStyle.danger, row=2)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import CategoryDetailView
        embed, view = CategoryDetailView.create_ui(self.bot, self.category_id, page=0)
        await interaction.response.edit_message(embed=embed, view=view)