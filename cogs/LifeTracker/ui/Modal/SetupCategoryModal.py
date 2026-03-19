import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class SetupCategoryModal(ui.Modal, title="⚙️ 新增自訂紀錄分類"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.category_name = ui.TextInput(label="主分類名稱", placeholder="例如：消費、健身、學習", max_length=20)
        self.add_item(self.category_name)

        self.fields_input = ui.TextInput(label="需要紀錄的數值 (用逗號分隔)", placeholder="例如：金額 (若是健身可填: 時間,消耗卡路里)", max_length=50)
        self.add_item(self.fields_input)

        self.subcats_input = ui.TextInput(label="子分類/標籤 (用逗號分隔)", placeholder="例如：飲食,通勤,娛樂,日用品", required=False, max_length=100)
        self.add_item(self.subcats_input)

    async def on_submit(self, interaction: discord.Interaction):
        cat_name = self.category_name.value.strip()
        fields_list = [f.strip() for f in self.fields_input.value.split(',') if f.strip()]
        subcats_list = [s.strip() for s in self.subcats_input.value.split(',') if s.strip()]

        try:
            # 💡 [關鍵修改] 呼叫 Manager，一行搞定所有資料庫操作！
            LifeTrackerDatabaseManager.create_category(
                user_id=interaction.user.id,
                username=interaction.user.name,
                cat_name=cat_name,
                fields_list=fields_list,
                subcats_list=subcats_list
            )

            # 建立成功畫面的 Embed
            embed = discord.Embed(
                title="✅ 分類建立成功！",
                description=(
                    f"**主分類**：{cat_name}\n"
                    f"**數值欄位**：{', '.join(fields_list)}\n"
                    f"**子分類**：{', '.join(subcats_list) if subcats_list else '無'}\n\n"
                    "**你可以點擊下方的「查看分類紀錄」來開始使用這個新分類！**"
                ),
                color=discord.Color.green()
            )
            
            # 刷新原本的 View
            from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
            view = LifeDashboardView(self.bot)
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 建立失敗: {e}", ephemeral=True)