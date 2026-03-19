import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class DynamicLogModal(ui.Modal):
    def __init__(self, bot, category_id: int, cat_name: str, fields: list, subcats: list):
        # Modal 標題長度最多 45 字元
        super().__init__(title=f"📝 紀錄：{cat_name}"[:45])
        self.bot = bot
        self.category_id = category_id
        
        # 1. 動態產生數值輸入框 (保留 2 個給子分類與備註，最多只能建 3 個動態欄位)
        self.field_inputs = {}
        for f in fields[:3]: 
            text_input = ui.TextInput(
                label=f,
                placeholder=f"請輸入 {f} 的數值",
                required=True,
                max_length=50
            )
            self.field_inputs[f] = text_input
            self.add_item(text_input)

        # 2. 加入「子分類」輸入框 (在 placeholder 提示他有哪些可以用)
        subcat_names = [s['name'] for s in subcats]
        subcat_placeholder = f"現有: {', '.join(subcat_names)}" if subcat_names else "可自訂新標籤"
        
        self.subcat_input = ui.TextInput(
            label="子分類 / 標籤 (選填)",
            placeholder=subcat_placeholder[:100], 
            required=False,
            max_length=20
        )
        self.add_item(self.subcat_input)

        # 3. 加入「備註」輸入框
        self.note_input = ui.TextInput(
            label="備註 (選填)",
            placeholder="例如：午餐吃麥當勞、深蹲破 PR",
            style=discord.TextStyle.short,
            required=False,
            max_length=100
        )
        self.add_item(self.note_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 收集動態欄位填寫的值，打包成 Dictionary
        values_dict = {}
        for f_name, input_ui in self.field_inputs.items():
            values_dict[f_name] = input_ui.value.strip()

        subcat_name = self.subcat_input.value.strip()
        note = self.note_input.value.strip()

        try:
            # 寫入資料庫
            LifeTrackerDatabaseManager.add_life_record(
                user_id=interaction.user.id,
                category_id=self.category_id,
                subcat_name=subcat_name,
                values_dict=values_dict,
                note=note
            )

            from cogs.LifeTracker.ui.View import CategoryDetailView
            embed, view = CategoryDetailView.create_ui(self.bot, self.category_id, page=0)
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 寫入紀錄失敗: {e}", ephemeral=True)