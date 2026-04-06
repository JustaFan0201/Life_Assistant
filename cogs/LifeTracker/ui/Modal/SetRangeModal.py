# cogs\LifeTracker\ui\Modal\SetRangeModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class SetRangeModal(ui.Modal, title="⏳ 新增自訂時間區間"):
    def __init__(self, bot, category_id):
        super().__init__()
        self.bot = bot
        self.category_id = category_id

        # 💡 將原本的 amount 改為更直覺的 days_input
        self.days_input = ui.TextInput(
            label="請輸入天數", 
            placeholder="例如：10 (天)、90 (天)...", 
            min_length=1, 
            max_length=4 # 支援到 9999 天
        )
        self.add_item(self.days_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. 取得輸入值並清理空白
        val = self.days_input.value.strip()
        
        try:
            days = int(val)
            if days <= 0:
                return await interaction.response.send_message("❌ 天數必須大於 0。", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ 請輸入有效的數字天數。", ephemeral=True)
        
        try:
            # 2. 更新資料庫：新增選項並設為當前檢視
            LifeTrackerDatabaseManager.add_range_option(self.category_id, days)
            LifeTrackerDatabaseManager.update_current_range(self.category_id, days)
            
            # 3. 先 defer，因為生成圖表需要時間
            await interaction.response.defer(ephemeral=False, thinking=False)

            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            # 重新生成看板介面
            embed, view, chart_file = await CategoryDetailView.create_ui(
                bot=self.bot, 
                category_id=self.category_id, 
                range_days=days
            )
            
            # 4. 更新原訊息（因為是從編輯模式跳轉回來，直接刷新看板）
            if chart_file:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])

        except Exception as e:
            print(f"❌ Modal 提交錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 發生錯誤時發送追蹤訊息
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ 設定失敗：{e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 設定失敗：{e}", ephemeral=True)