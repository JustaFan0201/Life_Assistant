import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class AddSubCategoryModal(ui.Modal, title="🏷️ 新增子分類"):
    def __init__(self, bot, category_id: int):
        super().__init__()
        self.bot = bot
        self.category_id = category_id

        self.subcat_name = ui.TextInput(
            label="子分類 / 標籤名稱",
            placeholder="例如：飲食、交通、娛樂...",
            required=True,
            max_length=20
        )
        self.add_item(self.subcat_name)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.subcat_name.value.strip()

        try:
            LifeTrackerDatabaseManager.add_subcategory(self.category_id, new_name)

            # 💡 [關鍵修改] 成功後，重新渲染 ManageSubcatView，而不是 DetailView
            from cogs.LifeTracker.ui.View import ManageSubcatView
            embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 新增子分類失敗: {e}", ephemeral=True)