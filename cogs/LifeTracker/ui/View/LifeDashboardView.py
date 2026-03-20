import discord
from discord import ui

from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal
from cogs.LifeTracker.ui.View.CategorySelectView import CategorySelectView
from database.db import DatabaseSession
from database.models import TrackerCategory

class LifeDashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        from cogs.System.ui.buttons import BackToMainButton
        self.add_item(BackToMainButton(self.bot))

    @staticmethod
    def create_dashboard(bot):
        embed = discord.Embed(
            title="📔 生活日記",
            description="歡迎來到你的生活日記！\n 請點擊下方按鈕來設定或查看你的分類紀錄。",
            color=discord.Color.blue()
        )
        embed.add_field(name="📂 查看分類紀錄", value="瀏覽你建立的分類，並進行記帳或追蹤", inline=False)
        embed.add_field(name="⚙️ 設定分類", value="自訂你想追蹤的新項目 (例如：記帳、健身)", inline=False)

        view = LifeDashboardView(bot)
        return embed, view

    @ui.button(label="查看分類紀錄", style=discord.ButtonStyle.success, emoji="📂", custom_id="life_view_records_btn")
    async def btn_view_records(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # 從資料庫撈取該使用者的所有主分類
        categories = []
        try:
            with DatabaseSession() as db:
                categories = db.query(TrackerCategory).filter(TrackerCategory.user_id == interaction.user.id).all()
        except Exception as e:
            await interaction.followup.send(f"❌ 讀取資料庫失敗: {e}", ephemeral=True)
            return

        if not categories:
            await interaction.followup.send("⚠️ 你目前還沒有建立任何分類喔！請先點擊「⚙️ 設定分類」。", ephemeral=True)
            return

        # 產生第二層的介面 (下拉選單)
        embed, view = CategorySelectView.create_ui(self.bot, categories)
        await interaction.edit_original_response(embed=embed, view=view)

    @ui.button(label="設定分類", style=discord.ButtonStyle.primary, emoji="⚙️", custom_id="life_setup_btn")
    async def btn_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupCategoryModal(self.bot))