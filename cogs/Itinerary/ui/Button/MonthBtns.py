import discord
from cogs.BasicDiscordObject import SafeButton
from datetime import datetime
from cogs.Itinerary import itinerary_config as conf
class PrevMonthBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(label="◀ 上個月", row=1, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        new_offset = max(0, self.parent_view.month_offset - 1)
        # 💡 加上 page=0，確保換月時回到第一頁
        embed, view, file = self.parent_view.__class__.create_ui(
            self.parent_view.cog, interaction.user.id, month_offset=new_offset, page=0
        )
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[file])

class NextMonthBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(label="下個月 ▶", row=1, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        # 💡 同步計算最大偏移量
        now = datetime.now(conf.TW_TZ)
        max_offset = conf.get_max_month_offset()
        
        new_offset = min(max_offset, self.parent_view.month_offset + 1)
        
        embed, view, file = self.parent_view.__class__.create_ui(
            self.parent_view.cog, interaction.user.id, month_offset=new_offset, page=0
        )
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[file])