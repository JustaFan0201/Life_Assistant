# cogs\LifeTracker\ui\Select\RangeSelect.py
import discord
from discord import ui
from cogs.Base import LockableView
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class RangeSelect(ui.Select):
    def __init__(self, bot, category_id, current_days, options_list, row=None):
        self.bot = bot
        self.category_id = category_id
        
        select_options = []
        actual_options = options_list if isinstance(options_list, list) else [7, 30, 180, 365]
        
        for d in actual_options:
            days_int = int(d)
            
            # 💡 自動換算邏輯：年 -> 月 -> 週 -> 天
            if days_int % 365 == 0:
                label = f"{days_int // 365} 年"
            elif days_int == 180: # 特殊處理半年
                label = "半年"
            elif days_int % 30 == 0:
                label = f"{days_int // 30} 個月"
            elif days_int % 7 == 0:
                label = f"{days_int // 7} 週"
            else:
                label = f"{days_int} 天"
            
            select_options.append(discord.SelectOption(
                label=label, 
                value=str(d), 
                emoji="⌛",
                default=(days_int == int(current_days))
            ))

        super().__init__(placeholder="⌛ 切換統計區間...", options=select_options, row=row)

    async def callback(self, interaction: discord.Interaction):
        # 💡 使用 defer 防止生成圖表時超時
        await interaction.response.defer()
        
        try:
            days = int(self.values[0])
            
            # 更新資料庫中的當前檢視區間
            LifeTrackerDatabaseManager.update_current_range(self.category_id, days)
            
            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            # 重新生成 UI
            embed, view, chart_file = await CategoryDetailView.create_ui(
                bot=self.bot, 
                category_id=self.category_id, 
                range_days=days
            )
            
            # 更新訊息
            if chart_file:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
                
        except Exception as e:
            print(f"❌ RangeSelect 出錯: {e}")
            import traceback
            traceback.print_exc()