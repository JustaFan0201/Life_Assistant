# cogs\LifeTracker\ui\Modal\EditSubcatNameModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.ui.View import ManageSubcatView
from cogs.LifeTracker.LifeTracker_config import (
    MAX_SUBCAT_LENGTH
)
class EditSubcatNameModal(ValidatedModal):
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
            max_length=MAX_SUBCAT_LENGTH
        )
        self.add_item(self.new_name_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        new_name = self.new_name_input.value.strip()
        
        success, error_msg = LifeTracker_Manager.update_subcategory_name(
            self.category_id, self.subcat_id, new_name
        )
        
        if not success:
            return error_msg
        return None

    async def on_success(self, interaction: discord.Interaction):
        try:
            from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
            embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
            embed.title = "✅ 標籤名稱已更新"
            embed.color = discord.Color.green()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"❌ 畫面刷新失敗：{e}", ephemeral=True)