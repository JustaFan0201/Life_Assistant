import discord
from discord import ui

from cogs.LifeTracker.ui.Modal import SetupCategoryModal

class SetupBtn(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="設定主分類", 
            style=discord.ButtonStyle.green, 
            emoji="⚙️", 
            custom_id="life_setup_btn",
            row=4
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetupCategoryModal(self.bot))