import discord
from discord import ui

class ViewCategorySelect(ui.Select):
    def __init__(self, bot, gmail_cog, user_id, categories):
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.categories_map = {str(c['id']): c['name'] for c in categories}
        
        options = [discord.SelectOption(label=c['name'], description=c['desc'][:50], value=str(c['id']), emoji="📂") for c in categories]
        super().__init__(placeholder="請選擇分類來查看信件...", min_values=1, max_values=1, options=options, row=2)

    async def callback(self, interaction: discord.Interaction):
        category_id = int(self.values[0])
        category_name = self.categories_map[str(category_id)]
        
        # 撈取資料庫中的信件
        emails = self.gmail_cog.db_manager.get_category_emails(category_id)
        
        from cogs.Gmail.ui.View.CategoryEmailPagerView import CategoryEmailPagerView
        pager_view = CategoryEmailPagerView(self.bot, self.gmail_cog, self.user_id, category_name, emails)
        
        await interaction.response.edit_message(embed=pager_view.generate_embed(), view=pager_view)