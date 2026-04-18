import discord
from discord import ui

class StockQueryBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="🔍 快速查詢",
            style=discord.ButtonStyle.secondary,
            custom_id="stock_quick_query",
            row=0 
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 延遲匯入 Modal，避免 Circular Import
        from ..Modal.StockQueryModal import StockQueryModal
        await interaction.response.send_modal(StockQueryModal(self.bot))