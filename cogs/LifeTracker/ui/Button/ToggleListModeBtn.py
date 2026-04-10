import discord
from cogs.BasicDiscordObject import SafeButton

class ToggleListModeBtn(SafeButton):
    def __init__(self, bot, category_id, page, field_index, is_showing_list, row=0):
        self.bot = bot
        self.category_id = category_id
        self.page = page
        self.field_index = field_index
        self.is_showing_list = is_showing_list
        
        style = discord.ButtonStyle.primary if not is_showing_list else discord.ButtonStyle.secondary
        emoji = "📊" if is_showing_list else "📋"
        
        super().__init__(label="", style=style, emoji=emoji, row=row)

    async def do_action(self, interaction: discord.Interaction):
        new_show_list = not self.is_showing_list
        target_page = 0 if new_show_list else self.page
        
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        embed, view, chart_file = await CategoryDetailView.create_ui(
            self.bot, self.category_id, page=target_page, field_index=self.field_index, show_list=new_show_list
        )
        
        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])