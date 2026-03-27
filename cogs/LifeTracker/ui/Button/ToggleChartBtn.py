import discord
from discord import ui
class ToggleChartBtn(ui.Button):
    def __init__(self, bot, category_id, current_field_index, fields_count, row=0):
        super().__init__(label="", style=discord.ButtonStyle.primary, emoji="🔄", row=row)
        self.bot = bot
        self.category_id = category_id
        self.current_field_index = current_field_index
        self.fields_count = fields_count

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # 計算下一個欄位的索引 (利用 % 餘數來達成循環：0 -> 1 -> 0)
        next_index = (self.current_field_index + 1) % self.fields_count
        
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        # 重新產生 UI，並把新的索引值傳進去！
        embed, view, chart_file = CategoryDetailView.create_ui(
            self.bot, self.category_id, page=0, field_index=next_index
        )

        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])