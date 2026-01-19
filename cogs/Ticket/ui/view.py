import discord
from discord import ui
import asyncio
from datetime import datetime, timedelta

# 引入定義好的按鈕
from ...System.ui.buttons import BackToMainButton
from .buttons import OpenTHSRQueryButton, BackToSearchBtn
from ..utils.thsr_scraper import get_thsr_schedule, STATION_MAP

# ====================================================
# 1. Ticket 主選單 (Dashboard)
# ====================================================
class TicketDashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(OpenTHSRQueryButton(bot))
        self.add_item(BackToMainButton(bot))


# ====================================================
# 2. 高鐵全功能查詢介面 (All-in-One)
# ====================================================
class THSRQueryView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- 預設狀態 ---
        self.start_station = None
        self.end_station = None
        self.date_val = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        self.time_val = "10:00"
        
        # 預設選項
        self.ticket_type = "全票" 
        self.trip_type = "單程"

        # --- 初始化選單選項 ---
        self.setup_dynamic_options()
        self.update_buttons()

    def setup_dynamic_options(self):
        """填入車站與日期選項"""
        
        # 1. 準備日期選項
        today = datetime.now()
        weekdays = ["(週一)", "(週二)", "(週三)", "(週四)", "(週五)", "(週六)", "(週日)"]
        
        # 3. 填入 Select 元件
        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                
                # --- 日期選單 ---
                if child.placeholder == "日期":
                    date_options = []
                    for i in range(25):
                        d = today + timedelta(days=i)
                        label = f"{d.strftime('%m/%d')} {weekdays[d.weekday()]}"
                        val = d.strftime("%Y/%m/%d")
                        is_default = (i == 1)
                        date_options.append(discord.SelectOption(label=label, value=val, default=is_default))
                    child.options = date_options

                # --- 起點選單 (關鍵修正：每次都生成新的 list) ---
                elif child.placeholder == "起點":
                    child.options = [
                        discord.SelectOption(label=name, value=name) 
                        for name in STATION_MAP.keys()
                    ]
                
                # --- 終點選單 (關鍵修正：每次都生成新的 list) ---
                elif child.placeholder == "終點":
                    child.options = [
                        discord.SelectOption(label=name, value=name) 
                        for name in STATION_MAP.keys()
                    ]

    # ================= UI 元件區 =================

    # [Row 0] 出發站
    @ui.select(placeholder="起點", row=0, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_start(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.start_station = select.values[0]
        await self.refresh_ui(interaction)

    # [Row 1] 抵達站
    @ui.select(placeholder="終點", row=1, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_end(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.end_station = select.values[0]
        await self.refresh_ui(interaction)

    # [Row 2] 出發日期
    @ui.select(placeholder="日期", row=2, min_values=1, max_values=1, options=[discord.SelectOption(label="載入中...", value="loading")])
    async def select_date(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.date_val = select.values[0]
        await self.refresh_ui(interaction)

    # [Row 3] 出發時間
    time_options_list = [
        discord.SelectOption(label=f"{h:02d}:00", value=f"{h:02d}:00", default=(h==10)) 
        for h in range(5, 24)
    ]
    @ui.select(placeholder="時間", row=3, options=time_options_list, min_values=1, max_values=1)
    async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.time_val = select.values[0]
        await self.refresh_ui(interaction)

    # [Row 4] 按鈕區
    @ui.button(label="查詢", style=discord.ButtonStyle.success, row=4, disabled=True)
    async def btn_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        status_desc = (
            f"🚄 **{self.start_station}** ➔ **{self.end_station}**\n"
            f"📅 {self.date_val} {self.time_val}\n"
            f"🎫 {self.trip_type} | {self.ticket_type}\n"
            f"⏳ 查詢中..."
        )
        loading_embed = discord.Embed(title="🔍 查詢中...", description=status_desc, color=discord.Color.blue())
        await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            result_data = await asyncio.to_thread(
                get_thsr_schedule, 
                self.start_station, 
                self.end_station, 
                self.date_val, 
                self.time_val
            )
            
            if isinstance(result_data, dict) and "data" in result_data:
                final_embed = discord.Embed(
                    title=f"🚄 {result_data['start']} ➔ {result_data['end']}",
                    description=f"📅 **{result_data['date']}** ({self.time_val} 後)\n🎫 {self.trip_type} / {self.ticket_type}",
                    color=0xec6c00
                )
                
                if not result_data['data']:
                     final_embed.description += "\n⚠️ 查無班次"
                else:
                    for train in result_data['data']:
                        field_value = (
                            f"`{train['dep']} ➔ {train['arr']}`\n"
                            f"⏱️ {train['duration']} | 🏷️ {train['discount']}"
                        )
                        final_embed.add_field(
                            name=f"🚅 {train['id']}", 
                            value=field_value, 
                            inline=True 
                        )

            elif isinstance(result_data, dict) and "error" in result_data:
                 final_embed = discord.Embed(title="❌ 查詢失敗", description=result_data['error'], color=discord.Color.red())
            else:
                final_embed = discord.Embed(title="❌ 未知錯誤", description=str(result_data), color=discord.Color.red())

            await interaction.edit_original_response(embed=final_embed, view=BackToSearchBtn(self.bot, self))
            
        except Exception as e:
            print(f"Scraper Error: {e}")
            error_embed = discord.Embed(title="❌ 系統錯誤", description=f"發生內部錯誤: {e}", color=discord.Color.red())
            await interaction.edit_original_response(embed=error_embed, view=BackToSearchBtn(self.bot, self))

    @ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=4)
    async def btn_swap(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.start_station, self.end_station = self.end_station, self.start_station
        await self.refresh_ui(interaction)

    @ui.button(label="全票", style=discord.ButtonStyle.secondary, row=4)
    async def btn_ticket_type(self, interaction: discord.Interaction, button: discord.ui.Button):
        types = ["全票", "大學生", "早鳥"]
        curr = types.index(self.ticket_type)
        self.ticket_type = types[(curr + 1) % len(types)]
        button.label = self.ticket_type 
        await self.refresh_ui(interaction)

    @ui.button(label="單程", style=discord.ButtonStyle.secondary, row=4)
    async def btn_trip_type(self, interaction: discord.Interaction, button: discord.ui.Button):
        types = ["單程", "來回"]
        curr = types.index(self.trip_type)
        self.trip_type = types[(curr + 1) % len(types)]
        button.label = self.trip_type 
        await self.refresh_ui(interaction)

    @ui.button(label="主頁", style=discord.ButtonStyle.danger, row=4)
    async def btn_home(self, interaction: discord.Interaction, button: discord.ui.Button):
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

    # ================= 邏輯處理區 =================

    def update_buttons(self):
        """檢查狀態並更新按鈕樣式"""
        search_btn = [x for x in self.children if isinstance(x, ui.Button) and x.label == "查詢"][0]
        
        btn_ticket = [x for x in self.children if isinstance(x, ui.Button) and x.label in ["全票", "大學生", "早鳥"]][0]
        btn_ticket.label = self.ticket_type
        
        btn_trip = [x for x in self.children if isinstance(x, ui.Button) and x.label in ["單程", "來回"]][0]
        btn_trip.label = self.trip_type

        if self.start_station and self.end_station:
            if self.start_station == self.end_station:
                search_btn.disabled = True
                search_btn.style = discord.ButtonStyle.danger
            else:
                search_btn.disabled = False
                search_btn.style = discord.ButtonStyle.success
        else:
            search_btn.disabled = True
            search_btn.style = discord.ButtonStyle.secondary

    async def refresh_ui(self, interaction: discord.Interaction):
        """重新整理介面"""
        self.update_buttons()
        
        for child in self.children:
            if isinstance(child, (ui.Select, discord.ui.Select)):
                target_val = None
                if child.placeholder == "日期": target_val = self.date_val
                elif child.placeholder == "時間": target_val = self.time_val
                elif child.placeholder == "起點": target_val = self.start_station
                elif child.placeholder == "終點": target_val = self.end_station
                
                # 重要：確保每個 child.options 都是獨立的列表，這樣修改 default 就不會互相影響
                # 但因為我們在 setup_dynamic_options 已經生成了獨立列表
                # 這裡只需要遍歷修改 default 即可
                
                if target_val:
                    for opt in child.options:
                        opt.default = (opt.value == target_val)

        embed = discord.Embed(title="🚄 高鐵時刻查詢設定", color=0xec6c00)
        embed.add_field(name="📍 起點", value=self.start_station or "未選", inline=True)
        embed.add_field(name="🏁 終點", value=self.end_station or "未選", inline=True)
        embed.add_field(name="📅 日期", value=self.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=self.time_val, inline=True)
        embed.add_field(name="🎫 票別", value=self.ticket_type, inline=True)
        embed.add_field(name="🔄 行程", value=self.trip_type, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)