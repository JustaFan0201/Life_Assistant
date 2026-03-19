import discord
from discord import ui

from cogs.LifeTracker.ui.Modal import SetupCategoryModal

class SetupBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="設定分類", 
            style=discord.ButtonStyle.primary, 
            emoji="⚙️", 
            custom_id="life_setup_btn"
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetupCategoryModal(self.bot))