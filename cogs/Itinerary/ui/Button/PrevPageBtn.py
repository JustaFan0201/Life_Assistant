import discord
from cogs.BasicDiscordObject import SafeButton

class PrevPageBtn(SafeButton):
    def __init__(self, parent_view, row=1):
        super().__init__(label="◀ 上一頁", row=row, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        new_page = max(0, self.parent_view.page - 1)
        
        kwargs = {'page': new_page}
        if hasattr(self.parent_view, 'month_offset'):
            kwargs['month_offset'] = self.parent_view.month_offset

        result = self.parent_view.__class__.create_ui(
            self.parent_view.cog, 
            interaction.user.id, 
            **kwargs
        )
        
        if len(result) == 3:
            embed, view, file = result
            attachments = [file]
        else:
            embed, view = result[0], result[1]
            attachments = []

        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view, attachments=attachments)
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=attachments)