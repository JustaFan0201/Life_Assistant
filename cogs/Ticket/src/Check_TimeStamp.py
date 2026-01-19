import discord
from discord.ext import commands
from discord import app_commands

# 引入 Dashboard View
from ..ui.view import TicketDashboardView

class THSR_CheckTimeStampCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[Ticket] CheckTimeStamp Module loaded.")

    def create_ticket_dashboard_ui(self):
        """
        回傳 Ticket 模組的主控台 Embed 和 View
        """
        embed = discord.Embed(
            title="🚄 高鐵服務中心",
            description="> 歡迎使用高鐵查詢系統，請選擇您需要的服務：",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        # 可以換成你喜歡的高鐵 Icon
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png")
        
        embed.add_field(
            name="功能說明", 
            value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次\n🎫 **票價查詢**：(開發中...)\n⚙️ **系統設定**：(開發中...)", 
            inline=False
        )
        
        embed.set_footer(text="Powered by Selenium • JustaFan0201")
        
        view = TicketDashboardView(self.bot)
        
        return embed, view
