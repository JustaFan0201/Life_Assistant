import discord
from discord import ui
class ToggleListModeBtn(ui.Button):
    def __init__(self, bot, category_id, page, field_index, is_showing_list, row=0):
        self.bot = bot
        self.category_id = category_id
        self.page = page
        self.field_index = field_index
        self.is_showing_list = is_showing_list
        
        # 根據目前的狀態，決定按鈕要長什麼樣子
        label = "" if is_showing_list else ""
        style = discord.ButtonStyle.primary if not is_showing_list else discord.ButtonStyle.secondary
        emoji = "📊" if is_showing_list else "📋"
        
        super().__init__(label=label, style=style, emoji=emoji, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # 狀態反轉：如果正在看列表，就切回 False；反之亦然
        new_show_list = not self.is_showing_list
        
        # 切換回列表時，順便把頁數歸零
        target_page = 0 if new_show_list else self.page
        
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        embed, view, chart_file = CategoryDetailView.create_ui(
            self.bot, self.category_id, page=target_page, field_index=self.field_index, show_list=new_show_list
        )
        
        if chart_file:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])