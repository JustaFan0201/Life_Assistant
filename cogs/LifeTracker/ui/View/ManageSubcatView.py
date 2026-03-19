import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

from cogs.LifeTracker.ui.Button import ToggleDeleteBtn,BackToDetailBtn,AddSubCategoryBtn

# --- 1. 刪除用的下拉選單 ---
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

        # 重新整理畫面，讓刪除的標籤消失
        embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
        await interaction.response.edit_message(embed=embed, view=view)


# --- 2. 管理面板本體 ---
class ManageSubcatView(ui.View):
    def __init__(self, bot, category_id: int, subcats_info: list, show_delete: bool = False):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id

        # 如果點擊了「刪除標籤」，就把下拉選單掛上去
        if show_delete and subcats_info:
            self.add_item(DeleteSubcatSelect(bot, category_id, subcats_info))

        # 1. 掛上你原本寫好的 [➕ 新增子分類] 按鈕
        self.add_item(AddSubCategoryBtn(bot, category_id))
        
        # 2. 如果有子分類才顯示 [🗑️ 刪除標籤] 按鈕
        if subcats_info:
            self.add_item(ToggleDeleteBtn(bot, category_id, subcats_info))

        self.add_item(BackToDetailBtn(bot, category_id))

    @staticmethod
    def create_ui(bot, category_id: int, show_delete: bool = False):
        cat_info, subcats_info = LifeTrackerDatabaseManager.get_category_details(category_id)

        embed = discord.Embed(
            title=f"⚙️ 管理標籤：{cat_info['name']}",
            description="這裡是該分類目前所有的專屬標籤。\n*(刪除標籤不會刪除過去的紀錄)*",
            color=discord.Color.orange()
        )

        if not subcats_info:
            embed.add_field(name="目前標籤清單", value="*目前沒有任何標籤喔！快點擊下方新增吧！*")
        else:
            subcat_list = "\n".join([f"• {s['name']}" for s in subcats_info])
            embed.add_field(name="目前標籤清單", value=f"```\n{subcat_list}\n```")

        return embed, ManageSubcatView(bot, category_id, subcats_info, show_delete)