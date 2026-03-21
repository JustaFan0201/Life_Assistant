import discord
from discord import ui

class PageBtn(ui.Button):
    def __init__(self, bot, category_id, target_page, label=None, emoji=None, row=1):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id
        self.target_page = target_page

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        embed, view = CategoryDetailView.create_ui(self.bot, self.category_id, self.target_page)
        await interaction.response.edit_message(embed=embed, view=view)