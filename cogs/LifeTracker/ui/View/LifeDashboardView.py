import discord
from cogs.System.ui.Button import BackToMainButton
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.LifeTracker.ui.Button.SetupBtn import SetupBtn
from cogs.LifeTracker.ui.Button.DeleteCategoryBtn import DeleteCategoryBtn
from cogs.LifeTracker.ui.Select.CategoryDashboardSelect import CategoryDashboardSelect
from cogs.BasicDiscordObject import LockableView
class LifeDashboardView(LockableView):
    def __init__(self, bot, categories=None):
        super().__init__(timeout=None)
        self.bot = bot
        
        if categories:
            self.add_item(CategoryDashboardSelect(self.bot, categories))
            
        deletable_categories = [c for c in categories if c.name != "消費"] if categories else []
        
        self.add_item(SetupBtn(self.bot, row=1))
        self.add_item(DeleteCategoryBtn(self.bot, deletable_categories, row=1))
        self.add_item(BackToMainButton(self.bot, row=1))

    @staticmethod
    def create_dashboard(bot, user_id: int):
        LifeTracker_Manager.ensure_default_consumption_category(user_id)
        categories = LifeTracker_Manager.get_user_categories(user_id)

        embed = discord.Embed(
            title="📔 生活日記",
            description="歡迎使用生活日記！你可以從下方選單快速切換分類，或是建立新分類。",
            color=discord.Color.blue()
        )
        if categories:
            cat_list_text = "\n".join([f"• **{c.name}** (`{', '.join(c.fields)}`)" for c in categories])
            embed.add_field(name="📂 我的分類清單", value=cat_list_text, inline=False)
        else:
            embed.add_field(name="📂 我的分類清單", value="目前還沒有建立任何分類喔！", inline=False)

        view = LifeDashboardView(bot, categories)
        return embed, view