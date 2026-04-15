# cogs\LifeTracker\ui\Modal\AddSubCategoryModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal 
from cogs.LifeTracker.LifeTracker_config import (
    MAX_SUBCATS,
    MAX_SUBCAT_LENGTH,
    MAX_TEXT_LENGTH
)

class AddSubCategoryModal(ValidatedModal):
    def __init__(self, bot, category_id: int):
        super().__init__(title="🏷️ 新增標籤")
        self.bot = bot
        self.category_id = category_id

        self.subcat_names_input = ui.TextInput(
            label=f"標籤名稱 (空白分隔，最多累積{MAX_SUBCATS}個，單個限制{MAX_SUBCAT_LENGTH}字)",
            placeholder="例如：飲食 交通 娛樂",
            required=True,
            max_length=MAX_TEXT_LENGTH
        )
        self.add_item(self.subcat_names_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        new_names = [n.strip() for n in self.subcat_names_input.value.split() if n.strip()]
        
        success, error_msg = LifeTracker_Manager.add_subcategory(self.category_id, new_names)
        
        if not success:
            return error_msg
        return None

    async def on_success(self, interaction: discord.Interaction):
        try:
            from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
            embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
            embed.title = "✅ 標籤新增成功！"
            embed.color = discord.Color.green()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"❌ 畫面刷新失敗: {e}", ephemeral=True)