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

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 執行預處理與標籤數量、長度、重複校驗"""
        self.new_names = [n.strip() for n in self.subcat_names_input.value.split() if n.strip()]
        
        if not self.new_names:
            return "請至少輸入一個標籤名稱。"

        # 檢查「這次輸入的內容」本身有無重複
        if len(self.new_names) != len(set(self.new_names)):
            return "輸入的標籤名稱中有重複項，請檢查。"

        # 取得現有標籤
        cat_info, current_subcats = LifeTracker_Manager.get_category_details(self.category_id)
        existing_names = [s['name'] for s in current_subcats] # 假設回傳的是 dict 格式

        # 檢查「新標籤」是否已存在於資料庫
        for name in self.new_names:
            if name in existing_names:
                return f"標籤「{name}」已經存在於此分類中，不需重複新增。"
            
            if len(name) > MAX_SUBCAT_LENGTH:
                return f"標籤「{name}」名稱過長，單一標籤請限制在 {MAX_SUBCAT_LENGTH} 個字以內。"

        # 總數校驗
        total_count = len(current_subcats) + len(self.new_names)
        if total_count > MAX_SUBCATS:
            return (f"標籤數量過多！該分類上限為 {MAX_SUBCATS} 個。")

        return None

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，寫入資料庫並刷新管理介面"""
        try:
            for name in self.new_names:
                LifeTracker_Manager.add_subcategory(self.category_id, name)

            # 重新獲取管理介面
            from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
            embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
            
            embed.title = "✅ 標籤新增成功！"
            embed.color = discord.Color.green()
            
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 系統寫入失敗: {e}", ephemeral=True)