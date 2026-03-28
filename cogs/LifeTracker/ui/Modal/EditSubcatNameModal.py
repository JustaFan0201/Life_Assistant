import discord
from discord import ui
from cogs.LifeTracker.utils.LifeTracker_Manager import LifeTrackerDatabaseManager

class EditSubcatNameModal(ui.Modal):
    def __init__(self, bot, category_id, subcat_id, old_name):
        super().__init__(title=f"📝 修改標籤：{old_name}")
        self.bot = bot
        self.category_id = category_id
        self.subcat_id = subcat_id

        self.new_name_input = ui.TextInput(
            label="新的標籤名稱",
            default=old_name,
            placeholder="請輸入新名稱...",
            required=True,
            max_length=20
        )
        self.add_item(self.new_name_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.new_name_input.value.strip()
        
        # 執行更新
        LifeTrackerDatabaseManager.update_subcategory_name(self.subcat_id, new_name)

        # 刷新管理介面
        from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
        embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
        embed.title = "✅ 標籤名稱已更新"
        await interaction.response.edit_message(embed=embed, view=view)