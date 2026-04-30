import discord
from discord import ui

class EditModeBtn(ui.Button):
    def __init__(self, bot, category_id):
        super().__init__(label="修改名稱", emoji="📝", style=discord.ButtonStyle.primary, row=1)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import ManageSubcatView
        embed, view =await ManageSubcatView.create_ui(self.bot, self.category_id, mode="edit")
        await interaction.response.edit_message(embed=embed, view=view)