# cogs\LifeTracker\ui\Modal\SetRangeModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal # 💡 引入父類

class SetRangeModal(ValidatedModal): # 💡 繼承父類
    def __init__(self, bot, category_id):
        super().__init__(title="⏳ 新增自訂時間區間")
        self.bot = bot
        self.category_id = category_id

        self.days_input = ui.TextInput(
            label="請輸入天數", 
            placeholder="例如：10 (天)、90 (天)...", 
            min_length=1, 
            max_length=4
        )
        self.add_item(self.days_input)

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 執行天數格式與範圍校驗"""
        val = self.days_input.value.strip()
        
        error = self.check_range(val, min_val=1, max_val=9999, field_name="天數")
        if error:
            return error
            
        return None

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，更新資料庫並刷新圖表看板"""
        try:
            days = int(self.days_input.value.strip())
            
            # 先 Defer，因為繪圖 (Matplotlib) 需要時間，避免 Interaction Expired
            # 這裡不使用 interaction.response.defer，因為 ValidatedModal 的 on_submit 
            # 已經處理了 response。但由於我們前面是 return None，response 尚未發出。
            await interaction.response.defer(ephemeral=False, thinking=False)

            # 2. 更新資料庫
            LifeTracker_Manager.add_range_option(self.category_id, days)
            LifeTracker_Manager.update_current_range(self.category_id, days)
            
            # 3. 重新生成看板介面
            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            embed, view, chart_file = await CategoryDetailView.create_ui(
                bot=self.bot, 
                category_id=self.category_id, 
                range_days=days
            )
            
            # 4. 更新原訊息（刷新看板與圖表）
            if chart_file:
                await interaction.edit_original_response(
                    embed=embed, 
                    view=view, 
                    attachments=[chart_file]
                )
            else:
                await interaction.edit_original_response(
                    embed=embed, 
                    view=view, 
                    attachments=[]
                )

        except Exception as e:
            print(f"❌ SetRangeModal 執行錯誤: {e}")
            await interaction.followup.send(f"❌ 設定失敗：{e}", ephemeral=True)