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

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 預處理清單並執行校驗"""
        # 取得主分類名稱 (先 strip 掉空格)
        cat_name = self.category_name.value.strip()
        
        # 預先處理字串轉為清單
        self.fields_list = [f.strip() for f in self.fields_input.value.split() if f.strip()]
        self.subcats_list = [s.strip() for s in self.subcats_input.value.split() if s.strip()]
        
        # 數量校驗
        if not self.fields_list:
            return "請至少輸入一個需要紀錄的數值項目（例如：金額）。"
        
        if len(self.fields_list) > MAX_FIELDS:
            return f"數值欄位過多（目前 {len(self.fields_list)} 個），最多只能設定 {MAX_FIELDS} 個。"
            
        if len(self.subcats_list) > MAX_SUBCATS:
            return f"標籤數量過多（目前 {len(self.subcats_list)} 個），最多只能設定 {MAX_SUBCATS} 個。"

        # 檢查「數值欄位」是否重複
        if len(self.fields_list) != len(set(self.fields_list)):
            return "數值欄位名稱不能重複，請檢查輸入。"

        # 檢查「標籤名稱」是否重複
        seen_subcats = set()
        for subcat in self.subcats_list:
            if subcat in seen_subcats:
                return f"標籤名稱「{subcat}」重複了，請檢查輸入。"
            seen_subcats.add(subcat)

        # 檢查單個「數值欄位」的字數
        for field in self.fields_list:
            if len(field) > MAX_FIELDS_LENGTH:
                return f"數值欄位「{field}」名稱過長，單一項目請限制在 {MAX_FIELDS_LENGTH} 個字以內。"

        # 檢查單個「標籤」的字數
        for subcat in self.subcats_list:
            if len(subcat) > MAX_SUBCAT_LENGTH:
                return f"標籤「{subcat}」名稱過長，單一標籤請限制在 {MAX_SUBCAT_LENGTH} 個字以內。"

        # 檢查是否與「現有主分類名稱」重複
        existing_categories = LifeTracker_Manager.get_user_categories(interaction.user.id)
        # 提取現有分類的名字 (轉成 list 以便比對)
        existing_names = [c.name for c in existing_categories]
        
        if cat_name in existing_names:
            return f"主分類「{cat_name}」已經存在，請換一個名字。"

        # 檢查主分類名稱長度
        return self.check_length(cat_name, min_len=1, max_len=MAX_MAINCAT_LENGTH, field_name="分類名稱")

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