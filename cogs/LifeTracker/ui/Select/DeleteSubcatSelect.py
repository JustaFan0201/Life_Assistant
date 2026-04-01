import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
class DeleteSubcatSelect(ui.Select):
    def __init__(self, bot, category_id, subcats):
        self.bot = bot
        self.category_id = category_id
        options = [discord.SelectOption(label=s['name'], value=str(s['id'])) for s in subcats]
        # 下拉選單預設會佔據一整列 (row=0)
        super().__init__(placeholder="🗑️ 請選擇要刪除的標籤...", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        subcat_id = int(self.values[0])
        # 刪除資料庫的該標籤
        LifeTrackerDatabaseManager.delete_subcategory(subcat_id)

        from cogs.LifeTracker.ui.View import ManageSubcatView
        # 重新整理畫面，讓刪除的標籤消失
        embed, view =await ManageSubcatView.create_ui(self.bot, self.category_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])