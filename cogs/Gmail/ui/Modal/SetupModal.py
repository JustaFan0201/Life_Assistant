# cogs/Gmail/ui/Modal/SetupModal.py
import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from ...utils.gmail_tool import EmailTools

class GmailSetupModal(ValidatedModal):
    def __init__(self, cog):
        super().__init__(title="設置個人 Gmail 服務")
        self.cog = cog
        
        self.address = ui.TextInput(label="Gmail 地址", placeholder="example@gmail.com", min_length=5)
        self.password = ui.TextInput(
            label="應用程式密碼", 
            placeholder="請輸入 Google 產生的 16 位密碼", 
            style=discord.TextStyle.short,
            min_length=16, 
            max_length=16
        )
        self.add_item(self.address)
        self.add_item(self.password)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        clean_address = EmailTools()._extract_pure_email(self.address.value)
        self.report = self.cog.db_manager.save_user_config(interaction.user.id, clean_address, self.password.value)
        
        if "❌" in self.report:
            return self.report
        return None

    async def on_success(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.report, ephemeral=True)