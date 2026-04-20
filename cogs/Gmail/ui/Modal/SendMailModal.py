# cogs/Gmail/ui/Modal/SendMailModal.py
import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from ...utils.gmail_tool import EmailTools

class EmailSendModal(ValidatedModal):
    def __init__(self, cog, user_id, to_default=""):
        super().__init__(title='寄件設定')
        self.cog = cog
        self.user_id = user_id
        
        self.to_input = ui.TextInput(label='收件人 gmail (必填)', default=to_default)
        self.subject_input = ui.TextInput(label='主旨', required=False)
        self.content_input = ui.TextInput(label='信件內容', style=discord.TextStyle.paragraph)
        
        self.add_item(self.to_input)
        self.add_item(self.subject_input)
        self.add_item(self.content_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        self.user_config = self.cog.db_manager.get_user_config(self.user_id)
        if not self.user_config:
            return "您尚未設置個人信箱。"
        
        self.clean_to = EmailTools()._extract_pure_email(self.to_input.value)
        return None 

    async def on_success(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            data = {'to': self.clean_to, 'subject': self.subject_input.value, 'content': self.content_input.value}
            user_tools = EmailTools(self.user_config['email'], self.user_config['password'])
            success, report = await user_tools.send_mail(data)
            await interaction.followup.send(f"{'✅' if success else '❌'} {report}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 系統執行出錯: {e}", ephemeral=True)

class EmailReplyModal(ValidatedModal):
    def __init__(self, cog, user_id, receiver, original_subject):
        super().__init__(title=f"回覆：{receiver[:20]}...")
        self.cog = cog
        self.user_id = user_id
        self.receiver = receiver
        self.subject = f"Re: {original_subject}" if not (original_subject and original_subject.startswith("Re:")) else original_subject
        
        self.content_input = ui.TextInput(label='回覆內容', style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.content_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        self.user_config = self.cog.db_manager.get_user_config(self.user_id)
        if not self.user_config:
            return "找不到您的信箱設定。"
        self.clean_receiver = EmailTools()._extract_pure_email(self.receiver)
        return None

    async def on_success(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = {'to': self.clean_receiver, 'subject': self.subject, 'content': self.content_input.value}
        user_tools = EmailTools(self.user_config['email'], self.user_config['password'])
        success, report = await user_tools.send_mail(data)
        await interaction.followup.send(f"{'✅' if success else '❌'} {report}", ephemeral=True)