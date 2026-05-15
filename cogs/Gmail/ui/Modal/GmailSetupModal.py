# cogs/Gmail/ui/Modal/SetupModal.py
import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from cogs.Gmail.utils import EmailTools

class GmailSetupModal(ValidatedModal):
    def __init__(self, cog):
        super().__init__(title="設置個人 Gmail 服務")
        self.cog = cog
        self.report = ""
        
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
        
        # 如果 report 中包含錯誤符號，代表失敗，回傳字串讓父類別彈出警告
        if "❌" in self.report:
            return self.report
            
        return "Success"

    async def on_success(self, interaction: discord.Interaction):
        """邏輯成功後，無痕刷新 Gmail 主控台介面"""
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        
        user_id = interaction.user.id
        embed, view = GmailDashboardView.create_ui(interaction.client, self.cog, user_id)
        
        if self.report:
            embed.description = f"**{self.report}**\n\n{embed.description}"
        
        # 編輯原本的 Dashboard 訊息，達成無痕切換
        await interaction.response.edit_message(embed=embed, view=view)