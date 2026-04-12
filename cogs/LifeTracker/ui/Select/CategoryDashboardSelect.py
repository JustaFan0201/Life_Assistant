# cogs\LifeTracker\ui\Select\CategoryDashboardSelect.py
import discord
from discord import ui
from cogs.BasicDiscordObject import LockableView
class CategoryDashboardSelect(ui.Select):
    def __init__(self, bot, categories):
        self.bot = bot
        options = []
        
        for cat in categories:
            is_dict = isinstance(cat, dict)
            c_name = cat['name'] if is_dict else cat.name
            c_fields = cat['fields'] if is_dict else cat.fields
            c_id = cat['id'] if is_dict else cat.id
            
            fields_str = ", ".join(c_fields) if c_fields else "無"
            
            options.append(discord.SelectOption(
                label=c_name[:25], 
                description=f"欄位: {fields_str}"[:50], 
                value=str(c_id),
                emoji="📂"
            ))
            
        super().__init__(
            placeholder="🔍 選擇一個分類來查看或紀錄...", 
            min_values=1, 
            max_values=1, 
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, LockableView):
            await self.view.lock_all(interaction)

        selected_category_id = int(self.values[0])
        from cogs.LifeTracker.ui.View import CategoryDetailView
        embed, view, chart_file = await CategoryDetailView.create_ui(
            self.bot, 
            selected_category_id, 
            page=0, 
            show_list=False
        )
        
        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])