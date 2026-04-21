import discord
from discord import ui

class StockBackToDashboardBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(label="返回股票儀表板", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from ..View.StockDashboardView import StockDashboardView
        
        # 產生儀表板 UI
        embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)