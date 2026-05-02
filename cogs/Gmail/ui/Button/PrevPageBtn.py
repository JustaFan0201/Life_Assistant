import discord
from discord import ui

class PrevPageBtn(ui.Button):
    def __init__(self, disabled: bool):
        super().__init__(label="◀ 上一頁", style=discord.ButtonStyle.secondary, disabled=disabled, row=0)

    async def callback(self, interaction: discord.Interaction):
        # 透過 self.view 取得父視圖 (CategoryEmailPagerView)
        view = self.view
        view.page -= 1
        
        # 刷新按鈕狀態與畫面
        view.clear_items()
        view._add_buttons()
        await interaction.response.edit_message(embed=view.generate_embed(), view=view)