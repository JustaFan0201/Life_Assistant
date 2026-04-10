import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.BasicDiscordObject import ValidatedModal

class SetupCategoryModal(ValidatedModal):
    def __init__(self, bot):
        super().__init__(title="⚙️ 新增自訂紀錄分類")
        self.bot = bot

        self.category_name = ui.TextInput(label="主分類名稱", placeholder="例如：消費、健身", max_length=20)
        self.add_item(self.category_name)

        self.fields_input = ui.TextInput(
            label="需要紀錄的數值 (空白分隔，最多3個)", 
            placeholder="例如：金額 次數", 
            max_length=50
        )
        self.add_item(self.fields_input)

        self.subcats_input = ui.TextInput(
            label="子分類/標籤 (空白分隔，最多20個)", 
            placeholder="例如：飲食 通勤 娛樂", 
            required=False, 
            max_length=200
        )
        self.add_item(self.subcats_input)

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 預處理清單並執行校驗"""
        # 預先處理字串轉為清單
        self.fields_list = [f.strip() for f in self.fields_input.value.split() if f.strip()]
        self.subcats_list = [s.strip() for s in self.subcats_input.value.split() if s.strip()]
        
        # 數量校驗
        if not self.fields_list:
            return "請至少輸入一個需要紀錄的數值項目（例如：金額）。"
        
        if len(self.fields_list) > 3:
            return f"數值欄位過多（目前 {len(self.fields_list)} 個），最多只能設定 3 個。"
            
        if len(self.subcats_list) > 20:
            return f"標籤數量過多（目前 {len(self.subcats_list)} 個），最多只能設定 20 個。"

        # 檢查分類名稱長度 (雖然有 max_length，但多一層 check 更好)
        return self.check_length(self.category_name.value.strip(), min_len=1, max_len=20, field_name="分類名稱")

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，執行資料庫寫入並重新渲染 Dashboard"""
        try:
            cat_name = self.category_name.value.strip()
            
            # 執行寫入
            LifeTracker_Manager.create_category(
                user_id=interaction.user.id,
                username=interaction.user.name,
                cat_name=cat_name,
                fields_list=self.fields_list,
                subcats_list=self.subcats_list
            )
            
            # 重新獲取 Dashboard 並顯示成功訊息
            from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            
            embed.title = "✅ 分類建立成功！"
            embed.description = (
                f"已成功建立 **{cat_name}** 分類。\n"
                f"數值欄位：`{'、'.join(self.fields_list)}`\n"
                f"預設標籤：`{'、'.join(self.subcats_list) if self.subcats_list else '無'}`\n\n"
                f"{embed.description}"
            )
            embed.color = discord.Color.green()
            
            # 更新原始訊息
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 系統建立失敗：{e}", ephemeral=True)