# cogs/Gmail/ui/Modal/ContactModals.py
import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from ...utils.gmail_tool import EmailTools

class AddEmailListModal(ValidatedModal):
    def __init__(self, cog, user_id):
        super().__init__(title="新增常用聯絡人")
        self.cog = cog
        self.user_id = user_id
        
        self.name_input = ui.TextInput(label="聯絡人暱稱", max_length=20)
        self.address_input = ui.TextInput(label="Email 地址")
        
        self.add_item(self.name_input)
        self.add_item(self.address_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        self.clean_address = EmailTools()._extract_pure_email(self.address_input.value)
        self.report = self.cog.db_manager.add_and_save(self.name_input.value, self.clean_address, self.user_id)
        
        if "❌" in self.report or "⚠️" in self.report:
            return self.report
        return None

    async def on_success(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.report, ephemeral=True)

class EditEmailModal(ValidatedModal):
    def __init__(self, cog, user_id, nickname):
        super().__init__(title="修改聯絡人資料")
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname
        
        self.email_input = ui.TextInput(label=f"修改 {nickname} 的 Email")
        self.add_item(self.email_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        self.clean_address = EmailTools()._extract_pure_email(self.email_input.value)
        self.result = self.cog.db_manager.update_contact(self.user_id, self.nickname, self.clean_address)
        
        if "❌" in self.result:
            return self.result
        return None

    async def on_success(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.result, ephemeral=True)