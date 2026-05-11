import discord
from cogs.BasicDiscordObject import SafeButton

class NextPageBtn(SafeButton):
    def __init__(self, parent_view, row=1):
        super().__init__(label="下一頁 ▶", row=row, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        # 🌟 [修正] 預先 defer()，防止 create_ui 運算過久導致「交互失敗」
        if not interaction.response.is_done():
            await interaction.response.defer()
            
        new_page = self.parent_view.page + 1
        
        kwargs = {'page': new_page}
        if hasattr(self.parent_view, 'month_offset'):
            kwargs['month_offset'] = self.parent_view.month_offset

        result = self.parent_view.__class__.create_ui(
            interaction.user.id, 
            **kwargs
        )
        
        if len(result) == 3:
            embed, view, file = result
            attachments = [file] if file else []
        else:
            embed, view = result[0], result[1]
            attachments = []

        await interaction.edit_original_response(embed=embed, view=view)