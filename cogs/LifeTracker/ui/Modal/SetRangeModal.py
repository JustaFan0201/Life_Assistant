# cogs\LifeTracker\ui\Modal\SetRangeModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class SetRangeModal(ui.Modal, title="⏳ 設定預設顯示區間"):
    def __init__(self, bot, category_id):
        super().__init__()
        self.bot = bot
        self.category_id = category_id

        self.amount = ui.TextInput(
            label="輸入數值", 
            placeholder="例如：1、3、12...", 
            min_length=1, max_length=2
        )
        self.unit = ui.TextInput(
            label="單位 (請輸入：週 / 月 / 年)", 
            placeholder="週、月、年 (不支援'天')", 
            min_length=1, max_length=1
        )
        self.add_item(self.amount)
        self.add_item(self.unit)

    async def on_submit(self, interaction: discord.Interaction):
        unit_map = {"週": 7, "月": 30, "年": 365}
        unit_val = self.unit.value.strip()
        
        # 1. 基本驗證
        if unit_val not in unit_map:
            return await interaction.response.send_message("❌ 單位錯誤！請輸入「週」、「月」或「年」。", ephemeral=True)
        
        try:
            days = int(self.amount.value.strip()) * unit_map[unit_val]
        except ValueError:
            return await interaction.response.send_message("❌ 數值請輸入數字。", ephemeral=True)
        
        try:
            # 更新資料庫
            LifeTrackerDatabaseManager.add_range_option(self.category_id, days)
            LifeTrackerDatabaseManager.update_current_range(self.category_id, days)
            
            await interaction.response.defer(ephemeral=False, thinking=False)

            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            embed, view, chart_file = await CategoryDetailView.create_ui(
                bot=self.bot, 
                category_id=self.category_id, 
                range_days=days
            )
            
            if chart_file:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])

        except Exception as e:
            print(f"❌ Modal 提交錯誤: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ 設定失敗：{e}", ephemeral=True)