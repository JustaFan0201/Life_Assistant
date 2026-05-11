import discord
from discord import ui

class StockBackToDashboardBtn(ui.Button):
    def __init__(self, bot, row=2):
        super().__init__(label="返回主介面", style=discord.ButtonStyle.danger, emoji="🔙", row=row)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.Stock.ui.View import StockDashboardView
        
        # 產生儀表板 UI
        embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)