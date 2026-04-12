import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager

class DeleteCategorySelect(ui.Select):
    def __init__(self, bot, categories):
        self.bot = bot
        options = [discord.SelectOption(label=f"刪除：{c.name}", value=str(c.id), emoji="🗑️") for c in categories]
        super().__init__(placeholder="⚠️ 請選擇要永久刪除的主分類...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_id = int(self.values[0])
        LifeTracker_Manager.delete_category(cat_id)
        
        # 刪除後跳回 Dashboard
        from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
        embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
        embed.title = "🗑️ 分類已刪除"
        await interaction.response.edit_message(embed=embed, view=view)