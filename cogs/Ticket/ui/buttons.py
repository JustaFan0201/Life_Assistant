import discord
from discord import ui

# 定義前往「查詢時刻表功能」的按鈕
class OpenTHSRQueryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="查詢時刻表", 
            style=discord.ButtonStyle.primary, 
            emoji="🗓️",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Lazy Import 避免循環引用
        from .select_view import THSRStationSelectView
        
        embed = discord.Embed(
            title="🚄 高鐵班次查詢",
            description="請透過下方選單選擇您的行程：",
            color=discord.Color.blue()
        )
        
        view = THSRStationSelectView(self.bot)
        view.fill_options() # 填入選項
        
        await interaction.response.edit_message(embed=embed, view=view)