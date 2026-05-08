import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from cogs.Gmail import MAX_CATEGORY_COUNT, MAX_CATEGORY_NAME_LENGTH, MAX_CATEGORY_DESC_LENGTH
class AddCategoryModal(ValidatedModal, title="✨ 新增郵件分類"):
    name = ui.TextInput(label="分類名稱", placeholder="例如：實習機會", max_length=MAX_CATEGORY_NAME_LENGTH)
    desc = ui.TextInput(
        label="分類判斷規則 (寫給 AI 看的)", 
        style=discord.TextStyle.paragraph, 
        placeholder="例如：包含任何公司的實習機會資訊", 
        max_length=MAX_CATEGORY_DESC_LENGTH
    )

    def __init__(self, gmail_cog, user_id):
        super().__init__()
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.success_msg = ""

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """
        執行資料庫寫入。
        父類別規定：成功回傳 None，失敗回傳錯誤字串。
        """
        current_categories = self.gmail_cog.db_manager.get_user_categories(self.user_id)
        if len(current_categories) >= MAX_CATEGORY_COUNT:
            return f"❌ 新增失敗：您的分類數量已達上限 ({MAX_CATEGORY_COUNT}個)！請先刪除不必要的分類。"
        success, msg = self.gmail_cog.db_manager.add_category(
            self.user_id, 
            self.name.value, 
            self.desc.value
        )
        
        if not success:
            return msg
            
        self.success_msg = msg
        return None

    async def on_success(self, interaction: discord.Interaction):
        """邏輯執行成功後，刷新主控台 UI"""
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        
        embed, view = GmailDashboardView.create_ui(interaction.client, self.gmail_cog, self.user_id)
        
        if self.success_msg:
            embed.description = f"🎉 **{self.success_msg}**\n\n{embed.description}"
            
        await interaction.response.edit_message(embed=embed, view=view)