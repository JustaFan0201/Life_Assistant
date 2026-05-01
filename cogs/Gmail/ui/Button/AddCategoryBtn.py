import discord
from discord import ui

class AddCategoryModal(ui.Modal, title="✨ 新增 AI 郵件分類"):
    name = ui.TextInput(label="分類名稱", placeholder="例如：繳費通知", max_length=20)
    desc = ui.TextInput(label="分類判斷規則 (寫給 AI 看的)", style=discord.TextStyle.paragraph, placeholder="例如：包含水費、電費、電信費的帳單或催繳通知", max_length=150)

    def __init__(self, gmail_cog, user_id):
        super().__init__()
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        success, msg = self.gmail_cog.db_manager.add_category(self.user_id, self.name.value, self.desc.value)
        
        # 重新整理畫面
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        embed, view = GmailDashboardView.create_ui(interaction.client, self.gmail_cog, self.user_id)
        
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.followup.send(msg, ephemeral=True)

class AddCategoryBtn(ui.Button):
    def __init__(self, gmail_cog, user_id):
        super().__init__(label="新增分類", style=discord.ButtonStyle.success, emoji="🏷️", row=1)
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddCategoryModal(self.gmail_cog, self.user_id))