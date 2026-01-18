import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

from ..ui.view import TicketDashboardView
from ..ui.select_view import THSRStationSelectView
from ..utils.thsr_scraper import get_thsr_schedule, STATION_MAP

class THSR_CheckTimeStampCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[Ticket] CheckTimeStamp Module loaded.")

    # 建立選項清單 (給 Slash Command 用)
    # discord.py 的 choices 需要是 app_commands.Choice 的列表
    station_choices_list = [
        app_commands.Choice(name=station, value=station) 
        for station in STATION_MAP.keys()
    ]

    # ---------------------------------------------------
    # 核心 UI 產生器
    # ---------------------------------------------------
    def create_ticket_dashboard_ui(self):
        """
        回傳 Ticket 模組的主控台 Embed 和 View
        """
        embed = discord.Embed(
            title="🚄 高鐵服務中心",
            description="> 請選擇您需要的服務：",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png")
        
        embed.add_field(name="功能說明", value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次", inline=False)
        embed.set_footer(text="Powered by Selenium")
        
        view = TicketDashboardView(self.bot)
        
        return embed, view

    # ---------------------------------------------------
    # Slash Commands (使用 app_commands)
    # ---------------------------------------------------

    # 1. 主動查詢指令 (爬蟲)
    @app_commands.command(name="thsr", description="查詢高鐵時刻表 (即時爬蟲)")
    @app_commands.describe(
        start="出發站", 
        end="抵達站", 
        date="日期 (格式 YYYY/MM/DD，不填預設明天)", 
        time="出發時間 (格式 HH:MM，預設 10:30)"
    )
    @app_commands.choices(start=station_choices_list, end=station_choices_list)
    async def thsr(
        self, 
        interaction: discord.Interaction, 
        start: app_commands.Choice[str], 
        end: app_commands.Choice[str], 
        date: str = None, 
        time: str = "10:30"
    ):
        # 1. 取得使用者選擇的值 (.value)
        start_station = start.value
        end_station = end.value

        # 2. 先 Defer (因為爬蟲會超過 3 秒)
        await interaction.response.defer()

        # 3. 驗證日期格式
        if date:
            try:
                datetime.strptime(date, "%Y/%m/%d")
            except ValueError:
                await interaction.followup.send("❌ 日期格式錯誤！請使用 `YYYY/MM/DD` (例如 2026/01/18)")
                return

        # 4. 背景執行爬蟲
        try:
            result = await asyncio.to_thread(
                get_thsr_schedule, 
                start_station=start_station, 
                end_station=end_station, 
                search_date=date, 
                search_time=time
            )
            
            # 5. 回傳結果 (使用 followup 因為已經 defer 過了)
            await interaction.followup.send(result)
            
        except Exception as e:
            await interaction.followup.send(f"❌ 查詢時發生未預期的錯誤: {e}")

    # 2. 快速查詢 (直接跳到選單)
    @app_commands.command(name="thsr_ui", description="[快捷] 開啟高鐵查詢選單")
    async def thsr_ui(self, interaction: discord.Interaction):
        """直接呼叫查詢選單"""
        view = THSRStationSelectView(self.bot)
        view.fill_options()
        await interaction.response.send_message("🚄 **快速查詢模式**\n請選擇行程：", view=view, ephemeral=True)

    # 3. 呼叫 Ticket 主控台
    @app_commands.command(name="ticket_dashboard", description="開啟高鐵服務主控台")
    async def ticket_dashboard(self, interaction: discord.Interaction):
        embed, view = self.create_ticket_dashboard_ui()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # 4. (管理員用) 發送常駐面板
    @app_commands.command(name="thsr_panel", description="[管理員用] 發送常駐查詢按鈕")
    @app_commands.checks.has_permissions(administrator=True)
    async def thsr_panel(self, interaction: discord.Interaction):
        # 這裡需要引入 OpenTHSRButton，避免循環引用建議在 function 內 import
        from ..ui.buttons import OpenTHSRQueryButton
        from discord.ui import View

        embed = discord.Embed(
            title="🚄 台灣高鐵 時刻表查詢",
            description="點擊下方按鈕開始查詢最新班次與票價資訊。",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Powered by Selenium Automation")
        
        # 建立一個簡單的 View 只放按鈕
        view = View()
        view.add_item(OpenTHSRQueryButton(self.bot))

        await interaction.response.send_message("面板已發送！", ephemeral=True)
        await interaction.channel.send(embed=embed, view=view)
