import discord
from discord import ui

class PageBtn(ui.Button):
    # 💡 1. 接收並儲存 field_index 與 show_list
    def __init__(self, bot, category_id, target_page, field_index=0, show_list=True, label=None, emoji=None, row=1):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id
        self.target_page = target_page
        self.field_index = field_index
        self.show_list = show_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        # 翻頁時，記得告訴系統「我還要繼續看列表 (show_list)，而且欄位是 field_index」
        embed, view, chart_file = CategoryDetailView.create_ui(
            self.bot, self.category_id, self.target_page, field_index=self.field_index, show_list=self.show_list
        )

        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])