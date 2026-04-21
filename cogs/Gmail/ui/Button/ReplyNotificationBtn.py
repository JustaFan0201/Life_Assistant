import discord
from discord import ui
from ..Modal.SendMailModal import EmailReplyModal

class ReplyNotificationBtn(ui.Button):
    def __init__(self, cog, email_info, target_user_id):
        super().__init__(label="快速回覆", style=discord.ButtonStyle.primary, emoji="✍️")
        self.cog = cog
        self.email_info = email_info
        self.target_user_id = target_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.target_user_id:
            await interaction.response.send_message("⚠️ 這不是您的郵件通知，無法回覆。", ephemeral=True)
            return
        modal = EmailReplyModal(self.cog, self.target_user_id, self.email_info['from'], self.email_info['subject'])
        await interaction.response.send_modal(modal)