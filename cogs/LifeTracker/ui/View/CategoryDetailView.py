import discord
from discord import ui
import matplotlib
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
import io

from cogs.LifeTracker.utils import LifeTrackerDatabaseManager, generate_donut_chart
from cogs.LifeTracker.ui.Button import BackToLifeDashboardBtn, LogRecordBtn, PageBtn, ManageSubcatBtn, ToggleChartBtn, ToggleListModeBtn

plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Taipei Sans TC Beta', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class CategoryDetailView(ui.View):
    def __init__(self, bot, category_id: int, page: int = 0, field_index: int = 0, fields_count: int = 1, show_list: bool = False):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        self.page = page
        self.field_index = field_index
        self.show_list = show_list

        self.add_item(LogRecordBtn(bot, category_id, row=0))
        self.add_item(ManageSubcatBtn(bot, category_id, row=0))
        
        self.add_item(ToggleListModeBtn(bot, category_id, page, field_index, show_list, row=0))
        
        if not show_list:
            # 【圖表模式】：只在多欄位且顯示圖表時，才給圖表切換按鈕
            if fields_count > 1:
                self.add_item(ToggleChartBtn(bot, category_id, field_index, fields_count, row=0))
        else:
            # 【列表模式】：只在顯示列表時，才給翻頁按鈕
            if page > 0:
                self.add_item(PageBtn(bot, category_id, page - 1, field_index, show_list, emoji="◀️", row=1))
            self.add_item(PageBtn(bot, category_id, page + 1, field_index, show_list, emoji="▶️", row=1))
            
        self.add_item(BackToLifeDashboardBtn(bot, row=1))

    @staticmethod
    def create_ui(bot, category_id: int, page: int = 0, field_index: int = 0, show_list: bool = False):
        cat_info, subcats_info = LifeTrackerDatabaseManager.get_category_details(category_id)
        if not cat_info:
            return discord.Embed(title="❌ 找不到該分類", color=discord.Color.red()), None, None

        fields = cat_info['fields']
        fields_count = len(fields)
        target_field = fields[field_index] if fields_count > 0 else None

        embed = discord.Embed(
            title=f"📊 分類看板：{cat_info['name']}",
            description=f"紀錄分類：`{', '.join(fields)}`\n目前焦點：**{target_field}**",
            color=discord.Color.gold()
        )

        chart_file = None
        
        # 根據模式決定要抓什麼資料
        if not show_list:
            # 【圖表模式】: 只抓統計數據畫圖
            stats_data = LifeTrackerDatabaseManager.get_subcat_stats(category_id, target_field)
            if stats_data:
                chart_file = generate_donut_chart(cat_info['name'], stats_data, target_field)
                if chart_file:
                    embed.set_image(url="attachment://chart.png")
            embed.description += "\n📋 數值明細 - 查看詳細紀錄列表。"
        
        else:
            # 【列表模式】: 不畫圖，只抓歷史紀錄
            embed.description += f"\n\n目前所在頁數：第 {page + 1} 頁"
            records = LifeTrackerDatabaseManager.get_recent_records(category_id, page=page, limit=10)
            
            if not records:
                embed.add_field(name="近期紀錄", value="這頁目前還沒有任何紀錄！請使用「📝 記錄」來新增吧！", inline=False)
            else:
                for r in records:
                    val_str = " | ".join([f"{k}: {v}" for k, v in r['values'].items()])
                    note_str = f"\n📝備註: {r['note']}" if r.get('note') else ""
                    embed.add_field(
                        name=f"🏷️ [{r['sub_name']}] - {r['created_at']}",
                        value=f"**{val_str}**{note_str}",
                        inline=False
                    )

        # 把當前狀態全部塞進去
        view = CategoryDetailView(bot, category_id, page, field_index, fields_count, show_list)
        return embed, view, chart_file