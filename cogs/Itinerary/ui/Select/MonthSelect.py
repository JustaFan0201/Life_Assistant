# cogs\Itinerary\ui\Select\MonthSelect.py
import discord
from datetime import datetime
from cogs.Itinerary import itinerary_config as conf

class MonthSelect(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        
        # 1. 取得當前時間與最大偏移量
        now = datetime.now(conf.TW_TZ)
        max_offset = conf.get_max_month_offset()
        
        options = []
        # 2. 動態生成所有可選的月份 (從 0 到 max_offset)
        for offset in range(max_offset + 1):
            # 計算該 offset 對應的實際年份與月份
            target_month = now.month + offset
            target_year = now.year + (target_month - 1) // 12
            target_month = (target_month - 1) % 12 + 1
            
            # 設定顯示標籤 (例如：2026 年 5 月)
            label = f"{target_year} 年 {target_month:02d} 月"
            
            # 如果是使用者目前正在看的月份，就設為預設值
            is_default = (offset == parent_view.month_offset)
            
            # emoji 可以加個小日曆圖示增加質感
            options.append(discord.SelectOption(
                label=label, 
                value=str(offset), 
                default=is_default,
                emoji="📆"
            ))

        super().__init__(placeholder="快速跳轉月份...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        # 1. 取得使用者選擇的月份偏移量 (value)
        new_offset = int(self.values[0])
        
        # 2. 呼叫產生器，並將 page 重置為 0
        embed, view, file = self.parent_view.__class__.create_ui(
            self.parent_view.cog, 
            interaction.user.id, 
            month_offset=new_offset, 
            page=0
        )
        
        # 3. 執行畫面更新
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[file])