# cogs\LifeTracker\ui\Modal\EditSubcatNameModal.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.ui.View import ManageSubcatView
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
            max_length=20
        )
        self.add_item(self.new_name_input)

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 執行名稱長度與內容校驗"""
        new_name = self.new_name_input.value.strip()
        
        # 使用父類的 check_length 檢查 (設定至少要 1 個字)
        error = self.check_length(new_name, min_len=1, max_len=20, field_name="標籤名稱")
        if error:
            return error
            
        # 額外檢查：如果名稱沒變，其實不需要提交資料庫
        # 雖然這不是錯誤，但可以回傳提示讓使用者知道沒改到
        # if new_name == self.old_name: return "新名稱不能與舊名稱相同。"
        
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