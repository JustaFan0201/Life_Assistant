import discord
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal

class AddCategoryModal(ValidatedModal, title="✨ 新增郵件分類"):
    name = ui.TextInput(label="分類名稱", placeholder="例如：實習機會", max_length=20)
    desc = ui.TextInput(
        label="分類判斷規則 (寫給 AI 看的)", 
        style=discord.TextStyle.paragraph, 
        placeholder="例如：包含任何公司的實習機會資訊", 
        max_length=150
    )

    def __init__(self, gmail_cog, user_id):
        super().__init__()
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.success_msg = ""  # 用來暫存成功訊息，傳遞給 on_success 使用

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """
        執行資料庫寫入。
        父類別規定：成功回傳 None，失敗回傳錯誤字串。
        """
        success, msg = self.gmail_cog.db_manager.add_category(
            self.user_id, 
            self.name.value, 
            self.desc.value
        )
        
        if not success:
            return msg  # 失敗時回傳錯誤訊息，ValidatedModal 會自動彈出警告並在3秒後刪除
            
        self.success_msg = msg
        return None  # 成功回傳 None，觸發下方的 on_success

    async def on_success(self, interaction: discord.Interaction):
        """邏輯執行成功後，刷新主控台 UI"""
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        
        # 重新生成主控台介面 (因為新增了分類，Select 選單需要更新)
        embed, view = GmailDashboardView.create_ui(interaction.client, self.gmail_cog, self.user_id)
        
        # 🌟 將成功提示直接插入 Embed 的描述最上方，取代原本的獨立訊息
        if self.success_msg:
            # 這樣原本的簡介文字會被往下推，最上面會顯示 🎉 ✅ 成功建立分類：XXX
            embed.description = f"🎉 **{self.success_msg}**\n\n{embed.description}"
            
            # 如果你比較喜歡改 Title 的話，就把上面那行註解掉，改用下面這行：
            # embed.title = f"🎉 {self.success_msg}"
        
        # 覆蓋原本的訊息
        await interaction.response.edit_message(embed=embed, view=view)