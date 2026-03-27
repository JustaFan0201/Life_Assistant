import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class AddSubCategoryModal(ui.Modal, title="🏷️ 新增標籤"):
    def __init__(self, bot, category_id: int):
        super().__init__()
        self.bot = bot
        self.category_id = category_id

        self.subcat_names = ui.TextInput(
            label="標籤名稱 (多個請用空白分隔)",
            placeholder="例如：飲食 交通 娛樂",
            required=True,
            max_length=150
        )
        self.add_item(self.subcat_names)

    async def on_submit(self, interaction: discord.Interaction):
        # 💡 支援空白分隔，並過濾掉空字串
        new_names = [n.strip() for n in self.subcat_names.value.split() if n.strip()]
        
        # 取得目前的詳細資訊（包含現有標籤）
        from cogs.LifeTracker.ui.View import ManageSubcatView
        cat_info, current_subcats = LifeTrackerDatabaseManager.get_category_details(self.category_id)
        
        # --- 數量檢查邏輯 ---
        total_count = len(current_subcats) + len(new_names)
        
        if total_count > 20:
            # 產生原本的介面，但在 Embed 中加上錯誤提示
            embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
            embed.title = "⚠️ 新增失敗：標籤過多"
            embed.description = (
                f"❌ 分類 **{cat_info['name']}** 的標籤上限為 20 個。\n"
                f"目前已有 {len(current_subcats)} 個，您試圖新增 {len(new_names)} 個。\n"
                f"請減少新增數量後再試。"
            )
            embed.color = discord.Color.red()
            return await interaction.response.edit_message(embed=embed, view=view)

        try:
            # 循環寫入資料庫
            for name in new_names:
                LifeTrackerDatabaseManager.add_subcategory(self.category_id, name)

            # 成功後，重新渲染管理介面
            embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
            embed.title = "✅ 標籤新增成功！"
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 新增標籤失敗: {e}", ephemeral=True)