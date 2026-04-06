# cogs/LifeTracker/ui/View/RangeEditView.py
import discord
from cogs.Base import LockableView
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.LifeTracker.ui.Select import RangeSelect
from cogs.LifeTracker.ui.Button import CustomRangeBtn,BackToDetailBtn
class RangeEditView(LockableView):
    def __init__(self, bot, category_id, options_list):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id

        self.add_item(RangeSelect(bot, category_id, 0, options_list, row=0, mode="delete"))

        self.add_item(CustomRangeBtn(bot, category_id, row=1))

        self.add_item(BackToDetailBtn(bot, category_id, label="返回看板", row=1))

    @staticmethod
    async def create_ui(bot, category_id):
        cat_info, _ = LifeTrackerDatabaseManager.get_category_details(category_id)
        options_list = cat_info.get('range_options') or [7, 30, 180, 365]

        embed = discord.Embed(
            title=f"⏳ 編輯時間區間：{cat_info['name']}",
            description=(
                "在此模式下，你可以：\n"
                "使用下方選單**刪除**不需要的快捷區間。\n"
                "點擊按鈕**新增**自訂的時間長度。\n\n"
                "注意：系統至少會保留一個區間。"
            ),
            color=discord.Color.blue()
        )
        
        view = RangeEditView(bot, category_id, options_list)
        return embed, view