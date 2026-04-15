import discord
from cogs.BasicDiscordObject import SafeButton

class PageBtn(SafeButton):
    def __init__(self, bot, category_id, target_page, field_index=0, show_list=True, label=None, emoji=None, row=1):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id
        self.target_page = target_page
        self.field_index = field_index
        self.show_list = show_list

    async def do_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        embed, view, chart_file = await CategoryDetailView.create_ui(
            self.bot, self.category_id, self.target_page, field_index=self.field_index, show_list=self.show_list
        )

        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])