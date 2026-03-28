import discord
from discord import ui
from cogs.System.ui.buttons import BackToMainButton
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.LifeTracker.ui.Button import SetupBtn,DeleteCategoryBtn
from cogs.LifeTracker.ui.Select import CategoryDashboardSelect

class LifeDashboardView(ui.View):
    def __init__(self, bot, categories=None):
        super().__init__(timeout=None)
        self.bot = bot
        
        if categories:
            self.add_item(CategoryDashboardSelect(self.bot, categories))
        
        self.add_item(SetupBtn(self.bot,row=1))
        self.add_item(DeleteCategoryBtn(self.bot, categories, row=1))
        self.add_item(BackToMainButton(self.bot,row=1))

    @staticmethod
    def create_dashboard(bot, user_id: int):
        categories = LifeTrackerDatabaseManager.get_user_categories(user_id)

        embed = discord.Embed(
            title="📔 生活日記",
            description="歡迎使用生活日記！你可以從下方選單快速切換分類，或是建立新分類。",
            color=discord.Color.blue()
        )
        embed.add_field(name="＋ 設定主分類", value="輸入你想記錄的項目來建立新的主分類！", inline=False)
        embed.add_field(name="－ 刪除主分類", value="選擇你想要刪除的分類！", inline=False)
        if categories:
            cat_list_text = "\n".join([f"• **{c.name}** (`{', '.join(c.fields)}`)" for c in categories])
            embed.add_field(name="📂 我的分類清單", value=cat_list_text, inline=False)
        else:
            embed.add_field(name="📂 我的分類清單", value="目前還沒有建立任何分類喔！", inline=False)

        view = LifeDashboardView(bot, categories)
        return embed, view