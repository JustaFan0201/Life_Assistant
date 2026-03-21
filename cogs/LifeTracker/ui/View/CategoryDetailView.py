import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.LifeTracker.ui.Button import BackToLifeDashboardBtn,LogRecordBtn,PageBtn,ManageSubcatBtn

class CategoryDetailView(ui.View):
    def __init__(self, bot, category_id: int, page: int = 0):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        self.page = page

        # 加入按鈕
        self.add_item(LogRecordBtn(bot, category_id))
        self.add_item(ManageSubcatBtn(bot, category_id))
        # 翻頁按鈕 (如果不在第一頁，顯示上一頁)
        if page > 0:
            self.add_item(PageBtn(bot, category_id, page - 1, "⬅️ 上一頁"))
        self.add_item(PageBtn(bot, category_id, page + 1, "➡️ 下一頁"))
        
        self.add_item(BackToLifeDashboardBtn(bot))
        
    @staticmethod
    def create_ui(bot, category_id: int, page: int = 0):
        # 1. 撈取分類與子分類資訊
        cat_info, subcats_info = LifeTrackerDatabaseManager.get_category_details(category_id)
        if not cat_info:
            return discord.Embed(title="❌ 找不到該分類", color=discord.Color.red()), None

        # 2. 撈取近期紀錄 (每頁顯示 10 筆)
        records = LifeTrackerDatabaseManager.get_recent_records(category_id, page=page, limit=10)

        # 3. 組裝 Embed 畫面
        embed = discord.Embed(
            title=f"📊 分類看板：{cat_info['name']}",
            description=f"目前所在頁數：第 {page + 1} 頁\n紀錄分類：`{', '.join(cat_info['fields'])}`",
            color=discord.Color.gold()
        )

        if not records:
            embed.add_field(name="近期紀錄", value="這頁目前還沒有任何紀錄！請使用「📝 記錄」來新增吧！*", inline=False)
        else:
            for r in records:
                val_str = " | ".join([f"{k}: {v}" for k, v in r['values'].items()])
                note_str = f" 📝備註: {r['note']}" if r['note'] else ""
                
                embed.add_field(
                    name=f"🏷️ [{r['sub_name']}] - {r['created_at']}",
                    value=f"**{val_str}**{note_str}",
                    inline=False
                )

        view = CategoryDetailView(bot, category_id, page)
        return embed, view