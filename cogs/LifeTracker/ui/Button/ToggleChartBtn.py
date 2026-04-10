# cogs\LifeTracker\ui\Button\ToggleChartBtn.py
import discord
from cogs.BasicDiscordObject import SafeButton

class ToggleChartBtn(SafeButton):
    def __init__(self, bot, category_id, current_field_index, fields_count, row=0):
        super().__init__(label="", style=discord.ButtonStyle.primary, emoji="🔄", row=row)
        self.bot = bot
        self.category_id = category_id
        self.current_field_index = current_field_index
        self.fields_count = fields_count

    async def do_action(self, interaction: discord.Interaction):
        next_index = (self.current_field_index + 1) % self.fields_count
        
        current_range = getattr(self.view, 'range_days', 7)
        
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        embed, view, chart_file = await CategoryDetailView.create_ui(
            self.bot, 
            self.category_id, 
            page=0, 
            field_index=next_index,
            range_days=current_range
        )

        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])