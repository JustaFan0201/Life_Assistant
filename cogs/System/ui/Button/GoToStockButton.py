import discord
from discord import ui

class GoToStockButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="股票監控", 
            style=discord.ButtonStyle.primary, 
            emoji="📈",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        try:
            from cogs.Stock.ui.View.StockDashboardView import StockDashboardView
            
            embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 股票模組跳轉失敗，原因：{e}", ephemeral=True)