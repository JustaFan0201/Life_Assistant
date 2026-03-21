import discord
from discord import ui
from cogs.LifeTracker.ui.Modal import SetupCategoryModal
from cogs.System.ui.buttons import BackToMainButton
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.LifeTracker.ui.Button import SetupBtn

class CategoryDashboardDropdown(ui.Select):
    def __init__(self, bot, categories):
        self.bot = bot
        options = []
        for cat in categories:
            fields_str = ", ".join(cat.fields)
            options.append(discord.SelectOption(
                label=cat.name,
                description=f"欄位: {fields_str}",
                value=str(cat.id),
                emoji="📂"
            ))
        super().__init__(placeholder="🔍 選擇一個分類來查看或紀錄...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_category_id = int(self.values[0])
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        embed, view = CategoryDetailView.create_ui(self.bot, selected_category_id, page=0)
        await interaction.response.edit_message(embed=embed, view=view)


class CategoryDashboardDropdown(ui.Select):
    def __init__(self, bot, categories):
        self.bot = bot
        options = []
        for cat in categories:
            fields_str = ", ".join(cat.fields)
            options.append(discord.SelectOption(
                label=cat.name,
                description=f"欄位: {fields_str}",
                value=str(cat.id),
                emoji="📂"
            ))
        super().__init__(placeholder="🔍 選擇一個分類來查看或紀錄...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_category_id = int(self.values[0])
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        embed, view = CategoryDetailView.create_ui(self.bot, selected_category_id, page=0)
        await interaction.response.edit_message(embed=embed, view=view)

class LifeDashboardView(ui.View):
    def __init__(self, bot, categories=None):
        super().__init__(timeout=None)
        self.bot = bot
        
        if categories:
            self.add_item(CategoryDashboardDropdown(self.bot, categories))
        
        self.add_item(SetupBtn(self.bot))
        self.add_item(BackToMainButton(self.bot))

    @staticmethod
    def create_dashboard(bot, user_id: int):
        categories = LifeTrackerDatabaseManager.get_user_categories(user_id)

        embed = discord.Embed(
            title="📔 生活日記",
            description="歡迎使用生活日記！你可以從下方選單快速切換分類，或是建立新分類。",
            color=discord.Color.blue()
        )
        embed.add_field(name="⚙️ 設定主分類", value="輸入你想記錄的項目來建立新的主分類！", inline=False)
        if categories:
            cat_list_text = "\n".join([f"• **{c.name}** (`{', '.join(c.fields)}`)" for c in categories])
            embed.add_field(name="📂 我的分類清單", value=cat_list_text, inline=False)
        else:
            embed.add_field(name="📂 我的分類清單", value="目前還沒有建立任何分類喔！", inline=False)

        view = LifeDashboardView(bot, categories)
        return embed, view