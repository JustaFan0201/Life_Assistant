# cogs\LifeTracker\ui\Select\RangeSelect.py
import discord
from discord import ui
from cogs.BasicDiscordObject import LockableView
from cogs.LifeTracker.utils import LifeTracker_Manager

class RangeSelect(ui.Select):
    def __init__(self, bot, category_id, current_days, options_list, row=None, mode="switch"):
        self.bot = bot
        self.category_id = category_id
        self.mode = mode
        
        select_options = []
        actual_options = options_list if isinstance(options_list, list) else [7, 30, 365]
        
        # 根據模式決定 Emoji 和 標籤前綴
        prefix = "🗑️ 刪除 " if mode == "delete" else ""
        main_emoji = "🗑️" if mode == "delete" else "⌛"

        for d in actual_options:
            days_int = int(d)
            
            # --- 💡 改良版複合時間換算邏輯 ---
            remaining_days = days_int
            parts = []
            
            # 1. 計算年 (365天)
            years = remaining_days // 365
            if years > 0:
                parts.append(f"{years} 年 ")
                remaining_days %= 365
            
            # 2. 計算月 (30天)
            months = remaining_days // 30
            if months > 0:
                parts.append(f"{months} 個月 ")
                remaining_days %= 30
                
            # 3. 計算週 (7天)
            weeks = remaining_days // 7
            if weeks > 0:
                parts.append(f"{weeks} 週 ")
                remaining_days %= 7
                
            # 4. 計算剩餘天數
            if remaining_days > 0 or not parts:
                parts.append(f"{remaining_days} 天 ")
            
            # 組合標籤 (例如: 1年1個月1天)
            label = "".join(parts)
            
            select_options.append(discord.SelectOption(
                label=f"{prefix}{label}", 
                value=str(d), 
                emoji=main_emoji,
                default=(days_int == int(current_days)) if mode == "switch" else False
            ))

        placeholder = "🗑️ 選擇要刪除的區間..." if mode == "delete" else "⌛ 切換統計區間..."
        super().__init__(placeholder=placeholder, options=select_options, row=row)

    async def callback(self, interaction: discord.Interaction):
        if self.mode == "switch":
            await interaction.response.defer()
        else:
            if isinstance(self.view, LockableView):
                await self.view.lock_all(interaction)

        try:
            days = int(self.values[0])

            if self.mode == "delete":
                success = LifeTracker_Manager.delete_range_option(self.category_id, days)
                
                from cogs.LifeTracker.ui.View.RangeEditView import RangeEditView
                embed, view = await RangeEditView.create_ui(self.bot, self.category_id)
                
                if not success:
                    embed.title = "❌ 刪除失敗"
                    embed.description = "無法刪除該選項，**系統必須保留至少一個時間區間**！\n\n" + embed.description
                    embed.color = discord.Color.red()
                
                if view:
                    await view.unlock_all() 

                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
            
            else:
                LifeTracker_Manager.update_current_range(self.category_id, days)
                
                from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
                embed, view, chart_file = await CategoryDetailView.create_ui(
                    bot=self.bot, category_id=self.category_id, range_days=days
                )
                
                if chart_file:
                    await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
                else:
                    await interaction.edit_original_response(embed=embed, view=view, attachments=[])
                
        except Exception as e:
            print(f"❌ RangeSelect [{self.mode}] 出錯: {e}")
            import traceback
            traceback.print_exc()
            if isinstance(self.view, LockableView):
                await self.view.unlock_all()