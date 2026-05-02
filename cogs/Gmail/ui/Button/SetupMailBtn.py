import discord
from discord import ui
from cogs.Gmail.ui.Modal import GmailSetupModal

class SetupMailBtn(ui.Button):
    def __init__(self, cog, row=1):
        super().__init__(label="設置信箱", style=discord.ButtonStyle.success, emoji="🔐",row=row)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GmailSetupModal(self.cog))