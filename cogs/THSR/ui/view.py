import discord
from discord import ui
from datetime import datetime, timedelta

# 引入 System 的按鈕
from ...System.ui.buttons import BackToMainButton

# 引入 Ticket 的按鈕邏輯
from .buttons import (
    OpenTHSRQueryButton, 
    THSRSearchButton, 
    THSRSwapButton, 
    THSRTicketTypeButton, 
    THSRTripTypeButton, 
    THSRHomeButton
)
from ..src.GetTimeStamp import STATION_MAP

# 1. THSR 主選單 (Dashboard)
class THSR_DashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(OpenTHSRQueryButton(bot))
        self.add_item(BackToMainButton(bot))

    @staticmethod
    def create_dashboard_ui(bot):
        embed = discord.Embed(
            title="🚄 高鐵服務中心",
            description="> 歡迎使用高鐵查詢系統，請選擇您需要的服務：",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png")
        embed.add_field(
            name="功能說明", 
            value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次\n🎫 **自動購票**：(開發中...)\n⚙️ **系統設定**：(開發中...)", 
            inline=False
        )
        embed.set_footer(text="Powered by Selenium • JustaFan0201")
        
        view = THSR_DashboardView(bot)
        return embed, view

# 2. 高鐵全功能查詢介面 (設定頁面)
class THSRQueryView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- 預設狀態 ---
        self.start_station = None
        self.end_station = None
        self.date_val = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        self.time_val = "10:00"
        self.ticket_type = "全票" 
        self.trip_type = "單程"

        # 初始化選單與按鈕
        self.setup_dynamic_options()
        self.search_btn = THSRSearchButton()
        self.add_item(self.search_btn)
        self.add_item(THSRSwapButton())
        self.ticket_btn = THSRTicketTypeButton(self.ticket_type)
        self.add_item(self.ticket_btn)
        self.trip_btn = THSRTripTypeButton(self.trip_type)
        self.add_item(self.trip_btn)
        self.add_item(THSRHomeButton(bot))

        self.update_buttons()

    @staticmethod
    def create_new_ui(bot):
        """
        [靜態方法] 產生一個全新的查詢介面 (預設值)
        """
        view = THSRQueryView(bot)
        # 使用下面的實例方法來產生 Embed
        embed = view.get_status_embed()
        return embed, view

    def get_status_embed(self):
        """
        [實例方法] 根據當前選擇的狀態，產生對應的 Embed
        這樣不管是 refresh_ui 還是 BackToSearch 都可以共用
        """
        embed = discord.Embed(title="🚄 高鐵時刻查詢設定", color=0xec6c00)
        embed.add_field(name="📍 起點", value=self.start_station or "未選", inline=True)
        embed.add_field(name="🏁 終點", value=self.end_station or "未選", inline=True)
        embed.add_field(name="📅 日期", value=self.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=self.time_val, inline=True)
        embed.add_field(name="🎫 票別", value=self.ticket_type, inline=True)
        embed.add_field(name="🔄 行程", value=self.trip_type, inline=True)
        return embed

    def setup_dynamic_options(self):
        today = datetime.now()
        weekdays = ["(週一)", "(週二)", "(週三)", "(週四)", "(週五)", "(週六)", "(週日)"]
        
        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                if child.placeholder == "日期":
                    date_options = []
                    for i in range(25):
                        d = today + timedelta(days=i)
                        label = f"{d.strftime('%m/%d')} {weekdays[d.weekday()]}"
                        val = d.strftime("%Y/%m/%d")
                        is_default = (i == 1)
                        date_options.append(discord.SelectOption(label=label, value=val, default=is_default))
                    child.options = date_options
                elif child.placeholder == "起點":
                    child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]
                elif child.placeholder == "終點":
                    child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]

    # ... (Select 元件部分保持不變) ...
    @ui.select(placeholder="起點", row=0, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_start(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.start_station = select.values[0]
        await self.refresh_ui(interaction)

    @ui.select(placeholder="終點", row=1, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_end(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.end_station = select.values[0]
        await self.refresh_ui(interaction)

    @ui.select(placeholder="日期", row=2, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_date(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.date_val = select.values[0]
        await self.refresh_ui(interaction)

    time_options_list = [discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=(h==10)) for h in range(5, 24)]
    @ui.select(placeholder="時間", row=3, options=time_options_list, min_values=1, max_values=1)
    async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.time_val = select.values[0]
        await self.refresh_ui(interaction)

    def update_buttons(self):
        self.ticket_btn.label = self.ticket_type
        self.trip_btn.label = self.trip_type
        if self.start_station and self.end_station:
            if self.start_station == self.end_station:
                self.search_btn.disabled = True
                self.search_btn.style = discord.ButtonStyle.danger
            else:
                self.search_btn.disabled = False
                self.search_btn.style = discord.ButtonStyle.success
        else:
            self.search_btn.disabled = True
            self.search_btn.style = discord.ButtonStyle.secondary

    async def refresh_ui(self, interaction: discord.Interaction):
        self.update_buttons()
        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                target_val = None
                if child.placeholder == "日期": target_val = self.date_val
                elif child.placeholder == "時間": target_val = self.time_val
                elif child.placeholder == "起點": target_val = self.start_station
                elif child.placeholder == "終點": target_val = self.end_station
                if target_val:
                    for opt in child.options:
                        opt.default = (opt.value == target_val)

        embed = self.get_status_embed()
        await interaction.response.edit_message(embed=embed, view=self)

# 3. 查詢結果頁面
class THSRResultView(ui.View):
    def __init__(self, bot, prev_view):
        super().__init__(timeout=None)
        self.bot = bot
        self.prev_view = prev_view 

    @ui.button(label="修改條件 / 重新查詢", style=discord.ButtonStyle.primary, emoji="🔙")
    async def back_to_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.prev_view.get_status_embed()
        
        embed.description = "已還原您的設定"
        await interaction.response.edit_message(embed=embed, view=self.prev_view)

    @ui.button(label="回主頁", style=discord.ButtonStyle.danger, emoji="🏠")
    async def back_to_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)