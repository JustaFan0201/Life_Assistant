import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

from cogs.LifeTracker.ui.Button import ToggleDeleteBtn,BackToDetailBtn,AddSubCategoryBtn,EditModeBtn
from cogs.LifeTracker.ui.Select import DeleteSubcatSelect,EditSubcatSelect

class ManageSubcatView(ui.View):
    def __init__(self, bot, category_id: int, subcats_info: list, mode: str = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id

        # 根據模式決定顯示哪個 Select
        if subcats_info:
            if mode == "delete":
                self.add_item(DeleteSubcatSelect(bot, category_id, subcats_info))
            elif mode == "edit":
                self.add_item(EditSubcatSelect(bot, category_id, subcats_info))

        # 功能按鈕
        self.add_item(AddSubCategoryBtn(bot, category_id))
        
        if subcats_info:
            self.add_item(EditModeBtn(bot, category_id))
            self.add_item(ToggleDeleteBtn(bot, category_id, subcats_info))

        self.add_item(BackToDetailBtn(bot, category_id))

    @staticmethod
    def create_ui(bot, category_id: int, mode: str = None):
        cat_info, subcats_info = LifeTrackerDatabaseManager.get_category_details(category_id)

        embed = discord.Embed(
            title=f"⚙️ 管理標籤：{cat_info['name']}",
            description="",
            color=discord.Color.orange()
        )
        embed.add_field(name="🏷️新增標籤", value="新增標籤到該分類中",inline=False)
        embed.add_field(name="📝修改名稱", value="修改該分類下標籤的名稱",inline=False)
        embed.add_field(name="🗑️刪除標籤", value="從該分類中刪除標籤",inline=False)
        embed.add_field(
            name="標籤列表", 
            value="這裡是該分類目前所有的專屬標籤。\n( 刪除標籤後，原紀錄將自動歸類至「其他」)", 
            inline=False
        )
        if not subcats_info:
            embed.add_field(name="目前標籤清單", value="*目前沒有任何標籤喔！快點擊下方新增吧！*")
        else:
            subcat_list = "\n".join([f"• {s['name']}" for s in subcats_info])
            embed.add_field(name="目前標籤清單", value=f"```\n{subcat_list}\n```")

        return embed, ManageSubcatView(bot, category_id, subcats_info, mode)