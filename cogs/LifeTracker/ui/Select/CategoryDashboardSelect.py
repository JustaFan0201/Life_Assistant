# cogs\LifeTracker\ui\Select\CategoryDashboardSelect.py
import discord
from discord import ui
from cogs.Base import LockableView

class CategoryDashboardSelect(ui.Select):
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
        if isinstance(self.view, LockableView):
            await self.view.lock_all(interaction)

        selected_category_id = int(self.values[0])
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        embed, view, chart_file = await CategoryDetailView.create_ui(self.bot, selected_category_id, page=0)
        
        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])