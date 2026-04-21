import discord
from discord import ui

class StockAddBtn(ui.Button):
    def __init__(self, bot, row=0):
        super().__init__(
            label="新增監控", 
            style=discord.ButtonStyle.primary, 
            emoji="➕", 
            row=row
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from ..Modal.StockAddModal import StockAddModal
        
        await interaction.response.send_modal(StockAddModal(self.bot))