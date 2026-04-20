import discord
from discord import ui
from ..Modal.SetupModal import GmailSetupModal

class SetupMailBtn(ui.Button): # ❌ 移除 SafeButton, ✅ 改為 ui.Button
    def __init__(self, cog):
        super().__init__(label="設置個人信箱", style=discord.ButtonStyle.success, emoji="🔐")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction): # ✅ 改為 callback
        await interaction.response.send_modal(GmailSetupModal(self.cog))