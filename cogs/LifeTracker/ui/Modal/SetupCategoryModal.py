import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.LifeTracker_config import (
    MAX_MAINCAT_LENGTH,
    MAX_FIELDS,
    MAX_FIELDS_LENGTH,
    MAX_SUBCATS,
    MAX_SUBCAT_LENGTH,
    MAX_TEXT_LENGTH
)

class SetupCategoryModal(ValidatedModal):
    def __init__(self, bot):
        super().__init__(title="⚙️ 新增自訂紀錄分類")
        self.bot = bot

        self.category_name = ui.TextInput(label=f"主分類名稱(長度限制{MAX_MAINCAT_LENGTH}個字)", placeholder="例如：消費、健身", max_length=MAX_MAINCAT_LENGTH)
        self.add_item(self.category_name)

        self.fields_input = ui.TextInput(
            label=f"需要紀錄的數值 (空白分隔，最多{MAX_FIELDS}個，單個長度限制{MAX_FIELDS_LENGTH}個字)", 
            placeholder="例如：金額 次數", 
            max_length=MAX_TEXT_LENGTH
        )
        self.add_item(self.fields_input)

        self.subcats_input = ui.TextInput(
            label=f"子分類/標籤 (空白分隔，最多{MAX_SUBCATS}個，單個長度限制{MAX_SUBCAT_LENGTH}個字)", 
            placeholder="例如：飲食 通勤 娛樂", 
            required=False, 
            max_length=MAX_TEXT_LENGTH
        )
        self.add_item(self.subcats_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """💡 呼叫 Manager 執行業務邏輯校驗"""
        fields_list = [f.strip() for f in self.fields_input.value.split() if f.strip()]
        subcats_list = [s.strip() for s in self.subcats_input.value.split() if s.strip()]
        cat_name = self.category_name.value.strip()

        # 呼叫 Manager 的靜態方法
        # 注意：我們直接在 validate_logic 執行 create，因為它包含校驗
        success, error_msg = LifeTracker_Manager.create_category(
            user_id=interaction.user.id,
            username=interaction.user.name,
            cat_name=cat_name,
            fields_list=fields_list,
            subcats_list=subcats_list
        )

        if not success:
            return error_msg

        return None

    async def on_success(self, interaction: discord.Interaction):
        """ 資料已在 validate_logic 存入，這裡只負責刷新 UI"""
        try:
            from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            
            embed.title = "✅ 分類建立成功！"
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 畫面更新失敗：{e}", ephemeral=True)