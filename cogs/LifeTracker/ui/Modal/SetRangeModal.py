# cogs\LifeTracker\ui\Modal\SetRangeModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.LifeTracker_config import (
    MAX_DAY_RANGE,
    MIN_DAY_RANGE
)
class SetRangeModal(ValidatedModal):
    def __init__(self, bot, category_id):
        super().__init__(title="⏳ 新增自訂時間區間")
        self.bot = bot
        self.category_id = category_id

        self.days_input = ui.TextInput(
            label=f"請輸入天數 ({MIN_DAY_RANGE}~{MAX_DAY_RANGE})", 
            placeholder="例如：10、90...", 
            min_length=1, 
            max_length=4 
        )
        self.add_item(self.days_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """💡 呼叫 Manager 執行業務邏輯校驗與資料寫入"""
        val = self.days_input.value.strip()
        
        success, error_msg = LifeTracker_Manager.add_range_option(self.category_id, val)
        
        if not success:
            return error_msg
            
        return None

    async def on_success(self, interaction: discord.Interaction):
        """💡 執行 UI 刷新與圖表生成"""
        try:
            days = int(self.days_input.value.strip())
            
            await interaction.response.defer(ephemeral=False, thinking=False)

            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            embed, view, chart_file = await CategoryDetailView.create_ui(
                bot=self.bot, 
                category_id=self.category_id, 
                range_days=days
            )
            
            attachments = [chart_file] if chart_file else []
            await interaction.edit_original_response(
                embed=embed, 
                view=view, 
                attachments=attachments
            )

        except Exception as e:
            print(f"❌ SetRangeModal UI 刷新失敗: {e}")
            await interaction.followup.send(f"❌ 畫面更新失敗：{e}", ephemeral=True)