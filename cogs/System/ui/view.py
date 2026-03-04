import discord
from discord import ui

# 引入按鈕
from .buttons import (
    StatusButton, 
    GoToTHSRButton, 
    GoToItineraryButton, 
    GoToGmailButton,
    OpenDashboardButton,
    GoToGPTButton
)

class SystemStartView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(OpenDashboardButton(bot))

    @staticmethod
    def create_start_ui(bot):
        """
        產生公共頻道的「啟動介面」
        """
        embed = discord.Embed(
            title="🤖 Life Assistant 啟動中心",
            description="點擊下方按鈕以開啟您的個人控制台。\n(控制台內容僅您可見，請安心使用)",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png")
        embed.set_footer(text="System Online • Ready to serve")
        
        view = SystemStartView(bot)
        return embed, view

class MainControlView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # 加入各個功能按鈕
        self.add_item(GoToTHSRButton(bot))
        self.add_item(GoToItineraryButton(bot))
        self.add_item(GoToGmailButton(bot)) # 修正: 這裡應該傳入 bot，原本寫 self.bot 也行但統一比較好
        self.add_item(StatusButton(bot))
        self.add_item(GoToGPTButton(bot))

    @staticmethod
    def create_dashboard_ui(bot):
        """
        [工廠模式] 統一產生 System Dashboard 的 Embed 與 View
        供所有「返回主選單」按鈕或指令呼叫使用。
        """
        embed = discord.Embed(
            title="Life Assistant 控制中心",
            description="> 歡迎使用全能助手，請點擊下方按鈕操作：",
            color=0x2b2d31,
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png")

        embed.add_field(name="🚄 高鐵工具", value="包含：高鐵時刻表查詢、定時訂票、線上訂票", inline=False)
        embed.add_field(name="📅 行程管理", value="規劃與查詢您的個人行程", inline=False)
        embed.add_field(name="📧 郵件管理", value="包含：新信即時通知、快速撰寫與寄送 Gmail", inline=False)
        embed.add_field(name="ℹ️ 系統狀態", value="檢查機器人延遲 (Ping)", inline=False)

        embed.set_footer(
            text="Life Assistant v0.1", 
            icon_url="https://cdn-icons-png.flaticon.com/512/906/906324.png"
        )

        view = MainControlView(bot)
        return embed, view