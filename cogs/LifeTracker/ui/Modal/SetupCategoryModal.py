import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class SetupCategoryModal(ui.Modal, title="⚙️ 新增自訂紀錄分類"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.category_name = ui.TextInput(label="主分類名稱", placeholder="例如：消費、健身", max_length=20)
        self.add_item(self.category_name)

        self.fields_input = ui.TextInput(
            label="需要紀錄的數值 (空白分隔，最多3個)", 
            placeholder="例如：金額 次數 (健身：時間 消耗卡路里)", 
            max_length=50
        )
        self.add_item(self.fields_input)

        self.subcats_input = ui.TextInput(
            label="子分類/標籤 (空白分隔，最多20個)", 
            placeholder="例如：飲食 通勤 娛樂 (健身：有氧 重訓)", 
            required=False, 
            max_length=200 # 增加長度以免標籤多時不夠打
        )
        self.add_item(self.subcats_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 使用 .split() 自動處理所有空白
        cat_name = self.category_name.value.strip()
        fields_list = [f.strip() for f in self.fields_input.value.split() if f.strip()]
        subcats_list = [s.strip() for s in self.subcats_input.value.split() if s.strip()]

        # 準備刷新的 Dashboard (為了獲取原始 Embed 樣式)
        from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
        embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)

        # --- 數量檢查邏輯 (改為修改 Embed 而不發送新訊息) ---
        error_msg = None
        if len(fields_list) > 3:
            error_msg = f"❌ **建立失敗**：數值欄位過多（目前 {len(fields_list)} 個），最多只能設定 3 個項目。"
        elif len(subcats_list) > 20:
            error_msg = f"❌ **建立失敗**：標籤數量過多（目前 {len(subcats_list)} 個），最多只能設定 20 個標籤。"
        elif not fields_list:
            error_msg = "❌ **建立失敗**：請至少輸入一個需要紀錄的數值項目。"

        if error_msg:
            embed.title = "⚠️ 輸入格式錯誤"
            embed.description = f"{error_msg}\n\n{embed.description}"
            embed.color = discord.Color.red()
            # 直接編輯原始訊息顯示錯誤
            return await interaction.response.edit_message(embed=embed, view=view)

        try:
            # 正常執行建立邏輯
            LifeTrackerDatabaseManager.create_category(
                user_id=interaction.user.id,
                username=interaction.user.name,
                cat_name=cat_name,
                fields_list=fields_list,
                subcats_list=subcats_list
            )
            
            # 重新獲取成功的 Dashboard 資料
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            
            embed.title = "✅ 分類建立成功！"
            embed.description = (
                f"已成功建立 **{cat_name}** 分類。\n"
                f"數值欄位：`{'、'.join(fields_list)}`\n"
                f"預設標籤：`{'、'.join(subcats_list) if subcats_list else '無'}`\n\n"
                f"{embed.description}" # 保留原本的說明文字
            )
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            embed.title = "❌ 系統建立失敗"
            embed.description = f"發生未知錯誤：{e}"
            embed.color = discord.Color.red()
            await interaction.response.edit_message(embed=embed, view=view)