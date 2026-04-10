# cogs\LifeTracker\ui\Modal\AddSubCategoryModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal 
from cogs.LifeTracker.ui.View import ManageSubcatView
class AddSubCategoryModal(ValidatedModal):
    def __init__(self, bot, category_id: int):
        super().__init__(title="🏷️ 新增標籤")
        self.bot = bot
        self.category_id = category_id

        self.subcat_names_input = ui.TextInput(
            label="標籤名稱 (多個請用空白分隔)",
            placeholder="例如：飲食 交通 娛樂",
            required=True,
            max_length=150
        )
        self.add_item(self.subcat_names_input)

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 執行預處理與標籤數量校驗"""
        self.new_names = [n.strip() for n in self.subcat_names_input.value.split() if n.strip()]
        
        if not self.new_names:
            return "請至少輸入一個標籤名稱。"

        cat_info, current_subcats = LifeTracker_Manager.get_category_details(self.category_id)
        
        total_count = len(current_subcats) + len(self.new_names)
        if total_count > 20:
            return (f"標籤上限為 20 個。目前已有 {len(current_subcats)} 個，"
                    f"您試圖新增 {len(self.new_names)} 個，將會超過限制。")

        return None

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，寫入資料庫並刷新管理介面"""
        try:
            for name in self.new_names:
                LifeTracker_Manager.add_subcategory(self.category_id, name)

            embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
            
            embed.title = "✅ 標籤新增成功！"
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 系統寫入失敗: {e}", ephemeral=True)