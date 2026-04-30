import discord
from discord import ui

class SetupBtn(ui.Button):
    def __init__(self, bot, label="設定主分類", emoji="➕", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.green, emoji=emoji, row=row)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
        await interaction.response.send_modal(SetupCategoryModal(self.bot))