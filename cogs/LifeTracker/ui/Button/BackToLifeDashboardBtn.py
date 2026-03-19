import discord
from discord import ui

class BackToLifeDashboardBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(label="返回", style=discord.ButtonStyle.danger, row=1)
        self.bot = bot
        
    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import LifeDashboardView
        embed, view = LifeDashboardView.create_dashboard(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)