import discord
from discord import ui

class OpenTHSRQueryButton(ui.Button):
    """
    [Dashboard] 用：點擊後開啟查詢介面
    """
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
        from .view import THSRQueryView
        
        # 初始化 View (預設: 單程、全票)
        view = THSRQueryView(self.bot)
        
        embed = discord.Embed(
            title="🚄 高鐵時刻查詢設定", 
            description="請透過下方選單調整您的行程", 
            color=0xec6c00
        )
        
        # 顯示初始狀態
        embed.add_field(name="📍 起點", value="未選", inline=True)
        embed.add_field(name="🏁 終點", value="未選", inline=True)
        embed.add_field(name="📅 日期", value=view.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=view.time_val, inline=True)
        embed.add_field(name="🎫 票別", value=view.ticket_type, inline=True)
        embed.add_field(name="🔄 行程", value=view.trip_type, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=view)


class BackToSearchBtn(ui.View):
    """
    [結果頁面] 用：包含「修改條件」與「回主頁」按鈕
    """
    def __init__(self, bot, prev_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.prev_view = prev_view # 這是 THSRQueryView 的實例 (保留了使用者的選擇)

    @ui.button(label="修改條件 / 重新查詢", style=discord.ButtonStyle.primary, emoji="🔙")
    async def back_to_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 還原到「設定頁面」
        embed = discord.Embed(title="🚄 高鐵時刻查詢設定", description="已還原您的設定", color=0xec6c00)
        
        # 從 prev_view 讀取使用者原本選好的值
        embed.add_field(name="📍 起點", value=self.prev_view.start_station, inline=True)
        embed.add_field(name="🏁 終點", value=self.prev_view.end_station, inline=True)
        embed.add_field(name="📅 日期", value=self.prev_view.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=self.prev_view.time_val, inline=True)
        embed.add_field(name="🎫 選項", value=f"{self.prev_view.trip_type} | {self.prev_view.ticket_type}", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self.prev_view)

    @ui.button(label="回主頁", style=discord.ButtonStyle.danger, emoji="🏠")
    async def back_to_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Lazy Import
        from .view import TicketDashboardView
        
        embed = discord.Embed(
            title="🚄 高鐵服務中心",
            description="> 請選擇您需要的服務：",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png")
        embed.add_field(name="功能說明", value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次", inline=False)
        embed.set_footer(text="Powered by Selenium")
        
        await interaction.response.edit_message(embed=embed, view=TicketDashboardView(self.bot))