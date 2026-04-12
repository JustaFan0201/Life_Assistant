# cogs\LifeTracker\ui\Select\DeleteCategorySelect.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager

class DeleteCategorySelect(ui.Select):
    def __init__(self, bot, categories):
        self.bot = bot
        options = [discord.SelectOption(label=f"刪除：{c.name}", value=str(c.id), emoji="🗑️") for c in categories]
        super().__init__(placeholder="⚠️ 請選擇要永久刪除的主分類...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'lock_all'):
            await self.view.lock_all(interaction)
        else:
            await interaction.response.defer() 

        try:
            cat_id = int(self.values[0])
            LifeTracker_Manager.delete_category(cat_id)
            
            from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            embed.title = "🗑️ 分類已刪除"
            
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            if hasattr(self.view, 'unlock_all'):
                await self.view.unlock_all(interaction)
            await interaction.followup.send(f"❌ 刪除失敗：{e}", ephemeral=True)