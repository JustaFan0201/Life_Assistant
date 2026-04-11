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

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 執行名稱長度與重複校驗"""
        new_name = self.new_name_input.value.strip()
        
        error = self.check_length(new_name, min_len=1, max_len=MAX_SUBCAT_LENGTH, field_name="標籤名稱")
        if error:
            return error
            
        # 檢查是否與現有標籤重複
        # 先抓取該分類的所有標籤詳情
        cat_info, current_subcats = LifeTracker_Manager.get_category_details(self.category_id)
        
        for subcat in current_subcats:
            if subcat['name'] == new_name and subcat['id'] != self.subcat_id:
                return f"標籤名稱「{new_name}」已存在，請換一個名字。"
        
        return None # 通過校驗

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，執行資料庫更新並刷新介面"""
        try:
            new_name = self.new_name_input.value.strip()
            
            # 執行資料庫更新
            LifeTracker_Manager.update_subcategory_name(self.subcat_id, new_name)

            # 重新渲染管理介面 (ManageSubcatView)
            embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
            
            embed.title = "✅ 標籤名稱已更新"
            embed.color = discord.Color.green()
            
            # 更新原始訊息
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"❌ 修改標籤名稱失敗: {e}")
            await interaction.response.send_message(f"❌ 系統更新失敗：{e}", ephemeral=True)