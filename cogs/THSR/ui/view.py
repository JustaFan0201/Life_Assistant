import discord
from discord import ui
from datetime import datetime, timedelta

# 引入 System 的按鈕
from ...System.ui.buttons import BackToMainButton

# 引入 Ticket 的按鈕邏輯
# ★★★ 注意：這裡必須包含所有在 View 裡用到的按鈕類別 ★★★
from .buttons import (
    OpenTHSRQueryButton, 
    OpenTHSRBookingButton,
    THSRSearchButton, 
    THSRBookingSearchButton,
    THSRSwapButton, 
    THSRSeatButton,
    THSRHomeButton
)
# 如果 THSRDatePageButton 是定義在 view.py 裡面的，就不需要從 buttons import

from ..src.GetTimeStamp import STATION_MAP

# =========================================================================
# 1. THSR 主選單 (Dashboard)
# =========================================================================
class THSR_DashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(OpenTHSRQueryButton(bot))
        self.add_item(OpenTHSRBookingButton(bot))
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
            value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次\n🎫 **自動購票**：自動化搶票系統", 
            inline=False
        )
        embed.set_footer(text="Powered by Selenium • JustaFan0201")
        
        view = THSR_DashboardView(bot)
        return embed, view

# =========================================================================
# 日期翻頁按鈕 (定義在 View 檔內，避免循環引用)
# =========================================================================
class THSRDatePageButton(ui.Button):
    def __init__(self):
        super().__init__(label="切換日期 (後段)", style=discord.ButtonStyle.secondary, emoji="📅", row=4)

    async def callback(self, interaction: discord.Interaction):
        self.view.date_page = 1 - self.view.date_page
        
        if self.view.date_page == 0:
            self.label = "切換日期 (後段)"
            self.style = discord.ButtonStyle.secondary
        else:
            self.label = "切換日期 (前段)"
            self.style = discord.ButtonStyle.primary
            
        self.view.setup_dynamic_options()
        await self.view.refresh_ui(interaction)

# =========================================================================
# 2. 高鐵全功能查詢介面 (Query View)
# =========================================================================
class THSRQueryView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.start_station = None
        self.end_station = None
        self.date_val = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        self.time_val = "10:00"
        self.ticket_type = "全票" 
        self.trip_type = "單程"
        self.date_page = 0 

        self.setup_dynamic_options()
        
        self.search_btn = THSRSearchButton()
        self.add_item(self.search_btn)
        self.add_item(THSRSwapButton())
        self.add_item(THSRDatePageButton())
        self.add_item(THSRHomeButton(bot))

        self.update_buttons()

    @staticmethod
    def create_new_ui(bot):
        view = THSRQueryView(bot)
        embed = view.get_status_embed()
        return embed, view

    def get_status_embed(self):
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
        all_date_options = []
        for i in range(35):
            d = today + timedelta(days=i)
            label = f"{d.strftime('%m/%d')} {weekdays[d.weekday()]}"
            val = d.strftime("%Y/%m/%d")
            is_default = (val == self.date_val)
            all_date_options.append(discord.SelectOption(label=label, value=val, default=is_default))

        start_idx = self.date_page * 25
        end_idx = start_idx + 25
        current_page_options = all_date_options[start_idx:end_idx]

        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                if child.placeholder == "日期":
                    child.options = current_page_options
                elif child.placeholder == "起點":
                    child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]
                elif child.placeholder == "終點":
                    child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]

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

# =========================================================================
# 4. 自動訂票介面 (Booking View)
# =========================================================================
class THSRBookingView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.start_station = None
        self.end_station = None
        self.date_val = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        self.time_val = "10:00"
        self.ticket_type = "全票" 
        self.trip_type = "單程"
        self.seat_prefer = "None" 
        self.date_page = 0 

        self.setup_dynamic_options()
        
        self.search_btn = THSRBookingSearchButton()
        self.add_item(self.search_btn)
        
        self.add_item(THSRSwapButton())
        
        # 新增：座位選擇按鈕
        self.seat_btn = THSRSeatButton(self.seat_prefer)
        self.add_item(self.seat_btn)
        
        self.add_item(THSRDatePageButton())
        
        self.add_item(THSRHomeButton(bot))

        self.update_buttons()

    @staticmethod
    def create_new_ui(bot):
        view = THSRBookingView(bot)
        embed = view.get_status_embed()
        return embed, view

    def get_status_embed(self):
        seat_text = {"None": "無", "Window": "靠窗", "Aisle": "走道"}
        embed = discord.Embed(title="🎫 高鐵自動訂票設定", description="本系統預設為 **單程 / 全票**", color=discord.Color.green())
        embed.add_field(name="📍 起點", value=self.start_station or "未選", inline=True)
        embed.add_field(name="🏁 終點", value=self.end_station or "未選", inline=True)
        embed.add_field(name="📅 日期", value=self.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=self.time_val, inline=True)
        embed.add_field(name="💺 座位", value=seat_text.get(self.seat_prefer, "無"), inline=True)
        return embed

    # --- 以下邏輯與 QueryView 相同，直接複製 ---
    def setup_dynamic_options(self):
        today = datetime.now()
        weekdays = ["(週一)", "(週二)", "(週三)", "(週四)", "(週五)", "(週六)", "(週日)"]
        all_date_options = []
        for i in range(35):
            d = today + timedelta(days=i)
            label = f"{d.strftime('%m/%d')} {weekdays[d.weekday()]}"
            val = d.strftime("%Y/%m/%d")
            is_default = (val == self.date_val)
            all_date_options.append(discord.SelectOption(label=label, value=val, default=is_default))

        start_idx = self.date_page * 25
        end_idx = start_idx + 25
        current_page_options = all_date_options[start_idx:end_idx]

        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                if child.placeholder == "日期": child.options = current_page_options
                elif child.placeholder == "起點": child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]
                elif child.placeholder == "終點": child.options = [discord.SelectOption(label=name, value=name) for name in STATION_MAP.keys()]

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
        seat_map = {"None": "座位: 無", "Window": "座位: 靠窗", "Aisle": "座位: 走道"}
        self.seat_btn.label = seat_map.get(self.seat_prefer, "座位: 無")

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

class THSRErrorView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # 加入回主頁按鈕
        self.add_item(THSRHomeButton(bot))

    @staticmethod
    def create_error_ui(bot, error_title, error_msg):
        """
        快速建立錯誤訊息 Embed 與 View
        """
        embed = discord.Embed(
            title=f"❌ {error_title}",
            description=f"系統遭遇預期外的狀況，請稍後再試。\n\n**錯誤詳情：**\n```{error_msg}```",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="請點擊下方按鈕返回主選單")
        
        view = THSRErrorView(bot)
        return embed, view