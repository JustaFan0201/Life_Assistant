import discord
from discord import ui
from datetime import datetime, timedelta, timezone

from ...System.ui.buttons import BackToMainButton

from database.db import DatabaseSession
from database.models import User,THSRProfile,Ticket,BookingSchedule

from .buttons import (
    OpenTHSRQueryButton, 
    OpenTHSRBookingButton,
    OpenTHSRProfileButton,
    THSRSearchButton, 
    THSRBookingSearchButton,
    THSRSwapButton, 
    THSRSeatButton,
    THSRHomeButton,
    OpenTHSRTicketsButton,
    THSRLoadEarlierButton,
    THSRLoadLaterButton,
    THSRResultEarlierButton,
    THSRResultLaterButton,
    ToggleScheduleButton,
    ToggleTicketsButton
)

from ..src.GetTimeStamp import STATION_MAP
TW_TZ = timezone(timedelta(hours=8))

class THSRTicketListView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # 加入切換到任務列表的按鈕
        self.add_item(ToggleScheduleButton(bot))
        # 加入回主頁按鈕
        self.add_item(THSRHomeButton(bot))

    @staticmethod
    def create_ticket_ui(bot, tickets: list[Ticket]):
        view = THSRTicketListView(bot)

        if not tickets:
            embed = discord.Embed(
                title="📂 我的車票庫",
                description="目前沒有任何訂票紀錄。\n請使用 **「線上訂票」** 功能來新增車票。",
                color=discord.Color.light_grey()
            )
            embed.set_footer(text="尚無資料")
            return embed, view

        embed = discord.Embed(
            title=f"📂 我的車票庫 ({len(tickets)} 筆)",
            description="以下顯示您最近的訂票紀錄：",
            color=discord.Color.blue()
        )
        
        for t in tickets:
            date_str = t.train_date
            route_str = f"{t.start_station} ➜ {t.end_station}"
            status_icon = "✅" if t.is_paid else "⚠️"
            status_text = "已付款" if t.is_paid else "未付款"
            
            field_name = f"{date_str} | {route_str}"
            field_value = (
                f"🚄 車次**{t.train_code}** ⏰ `{t.departure}` - `{t.arrival}`\n"
                f"🎫 代號: **`{t.pnr}`**\n"
                f"💺 座位: `{t.seats}`\n"
                f"💰 金額: {t.price} ({status_text} {status_icon})"
            )
            embed.add_field(name=field_name, value=field_value, inline=False)
        
        embed.set_footer(text="僅顯示最近 10 筆紀錄 • 請至高鐵官網付款/取票")
        return embed, view

class THSRScheduleListView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        # 加入切換回實體車票的按鈕
        self.add_item(ToggleTicketsButton(bot))
        # 加入回主頁按鈕
        self.add_item(THSRHomeButton(bot))

    @staticmethod
    def create_schedule_ui(bot, schedules: list[BookingSchedule]):
        view = THSRScheduleListView(bot)

        if not schedules:
            embed = discord.Embed(
                title="⏳ 我的定時搶票任務",
                description="目前沒有任何排程任務。\n請使用 **「定時訂票」** 功能來建立搶票排程。",
                color=discord.Color.light_grey()
            )
            embed.set_footer(text="尚無排程任務")
            return embed, view

        embed = discord.Embed(
            title=f"⏳ 我的定時搶票任務 ({len(schedules)} 筆)",
            description="以下顯示您設定的搶票排程紀錄：",
            color=discord.Color.orange()
        )
        
        status_map = {
            "pending": "等待中 ⏳",
            "processing": "執行中 🚀",
            "completed": "已完成 ✅",
            "failed": "失敗 ❌"
        }
        
        seat_map = {"Window": "靠窗", "Aisle": "走道", "None": "不指定"}

        for s in schedules:
            route_str = f"{s.start_station} ➜ {s.end_station}"
            status_text = status_map.get(s.status, s.status)
            seat_text = seat_map.get(s.seat_prefer, "不指定")
            
            # 格式化觸發時間
            t_time = s.trigger_time.strftime("%Y/%m/%d %H:%M:%S") if s.trigger_time else "未知"
            
            field_name = f"目標: {s.train_date} | {route_str}"
            field_value = (
                f"🚄 車次: **{s.train_code}次**\n"
                f"⏰ 啟動時間: `{t_time}`\n"
                f"💺 座位偏好: `{seat_text}`\n"
                f"📊 狀態: **{status_text}**"
            )
            embed.add_field(name=field_name, value=field_value, inline=False)
        
        embed.set_footer(text="僅顯示最近 10 筆任務紀錄")
        return embed, view

def mask_text(text, is_hidden=True):
    """隱碼處理輔助函式"""
    if not text: return "未設定"
    if not is_hidden: return text 
    if len(text) <= 6: return text 
    return text[:3] + "*" * (len(text) - 6) + text[-3:]

class THSRProfileModal(ui.Modal, title="設定高鐵個人檔案"):
    def __init__(self, bot, default_data, origin_view):
        super().__init__()
        self.bot = bot
        self.origin_view = origin_view 
        
        self.pid = ui.TextInput(label="身分證字號", placeholder="A123456789", default=default_data.get('pid'), min_length=10, max_length=10)
        self.phone = ui.TextInput(label="手機號碼", placeholder="09xxxxxxxx", default=default_data.get('phone'), required=False, max_length=10)
        self.email = ui.TextInput(label="電子郵件", placeholder="example@gmail.com", default=default_data.get('email'), required=False)
        self.tgo_id = ui.TextInput(label="TGo 會員帳號", placeholder="填寫 same 代表同身分證", default=default_data.get('tgo'), required=False)

        self.add_item(self.pid)
        self.add_item(self.phone)
        self.add_item(self.email)
        self.add_item(self.tgo_id)

    async def on_submit(self, interaction: discord.Interaction):
        discord_id = interaction.user.id
        username = interaction.user.name
        
        new_data = {
            'pid': self.pid.value,
            'phone': self.phone.value,
            'email': self.email.value,
            'tgo': self.tgo_id.value
        }

        try:
            with DatabaseSession() as db:
                # 1. 確保 User 存在
                user = db.query(User).filter(User.discord_id == discord_id).first()
                if not user:
                    user = User(discord_id=discord_id, username=username)
                    db.add(user)
                    db.flush() # 先 flush 產生 User 才能建立 Profile

                # 2. 查詢或建立 THSRProfile
                profile = db.query(THSRProfile).filter(THSRProfile.user_id == discord_id).first()
                if not profile:
                    profile = THSRProfile(user_id=discord_id)
                    db.add(profile)
                
                # 3. 更新 Profile 資料
                profile.personal_id = new_data['pid']
                profile.phone = new_data['phone']
                profile.email = new_data['email']
                profile.tgo_id = new_data['tgo']
                
                db.commit()

            self.origin_view.user_data = new_data
            self.origin_view.is_hidden = True 
            
            embed = self.origin_view.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self.origin_view)

        except Exception as e:
            await interaction.response.send_message(f"❌ 儲存失敗: {e}", ephemeral=True)

class THSRProfileView(ui.View):
    def __init__(self, bot, user_data):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_data = user_data 
        self.is_hidden = True 
        self.update_buttons()

    def generate_embed(self):
        status_icon = "🔒" if self.is_hidden else "🔓"
        status_text = "隱私模式 (已隱碼)" if self.is_hidden else "明碼模式 (請注意周圍視線)"
        color = discord.Color.green() if self.is_hidden else discord.Color.gold()

        embed = discord.Embed(title=f"👤 個人資料設定 {status_icon}", description=f"目前狀態：**{status_text}**", color=color)
        
        embed.add_field(name="🆔 身分證", value=mask_text(self.user_data.get('pid'), self.is_hidden), inline=False)
        embed.add_field(name="📱 手機", value=mask_text(self.user_data.get('phone'), self.is_hidden), inline=False)
        embed.add_field(name="📧 信箱", value=mask_text(self.user_data.get('email'), self.is_hidden), inline=False)
        embed.add_field(name="💎 TGo", value=self.user_data.get('tgo') if self.user_data.get('tgo') else "未設定", inline=False)
        
        embed.set_footer(text="點擊「修改」來編輯資料，點擊「顯示/隱藏」切換檢視")
        return embed

    def update_buttons(self):
        for child in self.children:
            if isinstance(child, ui.Button) and child.custom_id == "toggle_reveal":
                child.label = "顯示資料" if self.is_hidden else "隱藏資料"
                child.style = discord.ButtonStyle.secondary if self.is_hidden else discord.ButtonStyle.danger
                child.emoji = "👁️" if self.is_hidden else "🔒"

    @ui.button(label="修改資料", style=discord.ButtonStyle.primary, emoji="📝", row=0)
    async def edit_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(THSRProfileModal(self.bot, self.user_data, self))

    @ui.button(label="顯示資料", style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="toggle_reveal", row=0)
    async def toggle_reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_hidden = not self.is_hidden
        self.update_buttons() 
        embed = self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="回主選單", style=discord.ButtonStyle.secondary, emoji="↩️", row=1)
    async def back_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 直接呼叫下面的 class (同檔案，沒有循環引用問題)
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 1. THSR 主選單 (Dashboard)
class THSR_DashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(OpenTHSRQueryButton(bot))
        self.add_item(OpenTHSRBookingButton(bot))
        self.add_item(OpenTHSRProfileButton(bot))
        self.add_item(OpenTHSRTicketsButton(bot))
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
            name="🗓️**定時訂票**", 
            value="選擇想要預定的車次，並設定訂購時間，\n系統會在指定時間自動幫您訂購(會需要先輸入身分證)", 
            inline=False
        )
        embed.add_field(
            name="🎫**線上訂票**", 
            value="輸入車次條件，並選擇想要搭乘的車次，\n即可立即訂購目前高鐵平台剩餘車票(會需要先輸入身分證)", 
            inline=False
        )
        embed.add_field(
            name="📂**車票紀錄**", 
            value="查看您過去的車票資訊", 
            inline=False
        )
        embed.add_field(
            name="📝**設定個資**", 
            value="設定您的個人資料，包含身分證、手機、信箱與 TGo 資料，在訂票時會自動帶入", 
            inline=False
        )
        embed.set_footer(text="Powered by Selenium • JustaFan0201")
        
        view = THSR_DashboardView(bot)
        return embed, view

# 日期翻頁按鈕 (定義在 View 檔內，避免循環引用)
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

# 2. 高鐵查詢介面 (Query View)
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
        embed = discord.Embed(title="🚄高鐵預定車票 車次查詢", color=0xec6c00)
        embed.add_field(name="📍 起點", value=self.start_station or "未選", inline=True)
        embed.add_field(name="🏁 終點", value=self.end_station or "未選", inline=True)
        embed.add_field(name="📅 日期", value=self.date_val, inline=True)
        embed.add_field(name="⏰ 時間", value=self.time_val, inline=True)
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
    def __init__(self, bot, prev_view, driver=None): # 新增 driver 參數
        super().__init__(timeout=None)
        self.bot = bot
        self.prev_view = prev_view 
        self.driver = driver # 保存 driver 實例
        
        # 加入翻頁按鈕
        self.add_item(THSRResultEarlierButton())
        self.add_item(THSRResultLaterButton())

    # [重要] 當 View 超時或不再使用時，要關閉瀏覽器
    async def on_timeout(self):
        if self.driver:
            self.driver.quit()
            print("🕒 [THSRResultView] 瀏覽器已因逾時關閉")

    @ui.button(label="修改條件 / 重新查詢", style=discord.ButtonStyle.primary, emoji="🔙", row=2)
    async def back_to_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 按下返回時，也順便把目前的 driver 關掉，因為查詢頁面會開新的
        if self.driver:
            self.driver.quit()
            self.driver = None
            
        embed = self.prev_view.get_status_embed()
        await interaction.response.edit_message(embed=embed, view=self.prev_view)

    @ui.button(label="回高鐵主頁", style=discord.ButtonStyle.danger, emoji="🏠", row=2)
    async def back_to_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.driver:
            self.driver.quit()
            self.driver = None
            
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 4. 訂票介面 (Booking View)
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
        embed = discord.Embed(title="🎫高鐵線上訂票 車次查詢" , description="本系統預設為 **單程 / 全票**", color=discord.Color.green())
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

class THSRTrainSelect(ui.Select):
    def __init__(self, trains):
        options = []
        for t in trains[:25]: 
            discount_icon = ""
            raw_discount = t.get('discount', '')
            if "早鳥" in raw_discount: discount_icon = "🦅"
            elif "大學生" in raw_discount: discount_icon = "🎓"
            
            label = f"[{t['code']}] {t['departure']} ➜ {t['arrival']}"
            desc = f"⏱️ {t['duration']} {discount_icon} {raw_discount}"
            if len(desc) > 100: desc = desc[:97] + "..."
            
            options.append(discord.SelectOption(label=label, description=desc, value=t['code']))
        
        super().__init__(placeholder="👇 請選擇一班列車...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_code = self.values[0]
        user_data = {}
        
        # 1. 直接撈取個資 (不需再做防擋，因為前面按鈕已擋過)
        try:
            with DatabaseSession() as db:
                profile = db.query(THSRProfile).filter(THSRProfile.user_id == interaction.user.id).first()
                if profile:
                    user_data = {
                        'pid': profile.personal_id,
                        'phone': profile.phone,
                        'email': profile.email,
                        'tgo': profile.tgo_id
                    }
        except Exception as e:
            print(f"資料庫讀取錯誤: {e}")

        # 2. 直接執行自動訂票流程
        from .buttons import run_booking_flow
        await run_booking_flow(
            interaction, 
            self.view.bot, 
            self.view.driver, 
            selected_code, 
            user_data,
            self.view.start_st,
            self.view.end_st
        )

class THSRTrainSelectView(ui.View):
    def __init__(self, bot, driver, trains, start_st, end_st):
        super().__init__(timeout=None)
        self.bot = bot
        self.driver = driver
        self.trains = trains
        self.start_st = start_st
        self.end_st = end_st
        
        self.add_item(THSRTrainSelect(trains))

        self.add_item(THSRLoadEarlierButton())
        self.add_item(THSRLoadLaterButton())

    @staticmethod
    def create_train_selection_ui(bot, driver, trains, start_st, end_st):

        embed = discord.Embed(
            title="🚄 請選擇車次 (自動訂票)", 
            description=f"✅ 已為您找到 **{len(trains)}** 班列車\n請在下方選單選擇，或使用按鈕切換時段：",
            color=discord.Color.green()
        )
        
        for t in trains[:10]:
            discount = t.get('discount', '無')
            display_disc = "🏷️ 原價"
            if "早鳥" in discount: display_disc = f"🦅 **{discount}**"
            elif "大學生" in discount: display_disc = f"🎓 **{discount}**"
            elif discount != "無優惠" and discount: display_disc = f"🏷️ {discount}"
            
            val = f"⏱️ 行車: `{t['duration']}` | {display_disc}"
            embed.add_field(
                name=f"🚅 {t['code']} 次 | {t['departure']} ➜ {t['arrival']}", 
                value=val, 
                inline=False
            )

        if len(trains) > 10:
            embed.set_footer(text=f"還有 {len(trains)-10} 班車未列出，請查看下拉選單完整列表")
        else:
            embed.set_footer(text="請從下拉選單選擇您要搭乘的班次")

        view = THSRTrainSelectView(bot, driver, trains, start_st, end_st)
        
        return embed, view

    # 取消按鈕也可以搬去 buttons.py，或者暫時留在這裡
    @ui.button(label="取消訂票 (返回設定)", style=discord.ButtonStyle.danger, row=4)
    async def cancel_booking(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        if self.driver:
            self.driver.quit()
            
        # 使用區域引用呼叫 BookingView
        from .view import THSRBookingView
        embed, view = THSRBookingView.create_new_ui(self.bot)
        embed.description = "❌ 上一次訂票已取消，請重新設定條件。"
        embed.color = discord.Color.red()
        
        await interaction.edit_original_response(embed=embed, view=view)

class THSRSuccessView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(THSRHomeButton(bot))

    @staticmethod
    def create_booking_success_ui(bot, final_result, start_st=None, end_st=None):
        """
        [工廠方法] 產生訂票成功的 Embed 與 View
        """
        embed = discord.Embed(title="🎉 訂位成功！", color=discord.Color.green())
        embed.add_field(name="訂位代號", value=f"`{final_result['pnr']}`", inline=False)
        embed.add_field(name="總金額", value=final_result['price'], inline=True)
        embed.add_field(name="狀態", value=final_result['payment_status'], inline=True)
        
        # 顯示起訖站 (如果有的話)
        route_str = f"{start_st} ➜ {end_st}" if (start_st and end_st) else "詳見官網"
        
        train_info = final_result['train']
        train_str = (
            f"🚄 **{train_info.get('code')} 次**\n"
            f"📅 {train_info.get('date')}\n"
            f"⏰ {train_info.get('dep_time')} - {train_info.get('arr_time')}\n"
            f"📍 {route_str}"
        )
        embed.add_field(name="車次資訊", value=train_str, inline=False)
        embed.add_field(name="座位", value=", ".join(final_result['seats']), inline=False)
        
        embed.set_footer(text="請記得前往高鐵官網或 App 付款", icon_url="https://cdn-icons-png.flaticon.com/512/7518/7518748.png")
        
        view = THSRSuccessView(bot)
        return embed, view

class THSRErrorView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(THSRHomeButton(bot))

    @staticmethod
    def create_error_ui(bot, error_title, error_msg):
        embed = discord.Embed(
            title=f"❌ {error_title}",
            description=f"系統遭遇預期外的狀況，請稍後再試。\n\n**錯誤詳情：**\n```{error_msg}```",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="請點擊下方按鈕返回主選單")
        
        view = THSRErrorView(bot)
        return embed, view

class THSRScheduleModal(ui.Modal, title="⏰ 設定定時搶票"):
    def __init__(self, bot, train_code, start_st, end_st, train_date):
        super().__init__()
        self.bot = bot
        self.train_code = train_code
        self.start_st = start_st
        self.end_st = end_st
        self.train_date = train_date # 這是車次的出發日期 (固定)

        # 取得台北現在時間作為預設值
        tw_now = datetime.now(TW_TZ)
        default_trigger_date = tw_now.strftime("%Y/%m/%d")
        default_trigger_time = (tw_now + timedelta(minutes=5)).strftime("%H:%M:%S")
        
        # 1. [新增] 啟動日期輸入框
        self.trigger_date = ui.TextInput(
            label="預定啟動日期 (YYYY/MM/DD)", 
            placeholder="例如 2026/02/15",
            default=default_trigger_date, # 預設為今天
            min_length=10, 
            max_length=10
        )
        self.add_item(self.trigger_date)

        # 2. 啟動時間輸入框
        self.trigger_time = ui.TextInput(
            label="預定啟動時間 (HH:MM:SS)", 
            placeholder="例如 00:00:05",
            default=default_trigger_time,
            min_length=8, 
            max_length=8
        )
        self.add_item(self.trigger_time)

        # 3. 座位偏好輸入框
        self.seat_input = ui.TextInput(
            label="座位偏好 (選填)",
            placeholder="請輸入：靠窗、走道 (留空則不指定)",
            required=False,
            max_length=10
        )
        self.add_item(self.seat_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 讀取輸入值
        t_date_str = self.trigger_date.value.strip()
        t_time_str = self.trigger_time.value.strip()
        seat_str = self.seat_input.value.strip()
        
        # --- 解析座位偏好 ---
        final_seat_prefer = "None"
        if "靠窗" in seat_str or "window" in seat_str.lower():
            final_seat_prefer = "Window"
        elif "走道" in seat_str or "aisle" in seat_str.lower():
            final_seat_prefer = "Aisle"
        
        # --- 解析啟動時間 (日期 + 時間) ---
        target_time = None
        try:
            # 1. 組合字串
            full_time_str = f"{t_date_str} {t_time_str}"
            
            # 2. 解析為 datetime (尚未帶時區)
            target_time_naive = datetime.strptime(full_time_str, "%Y/%m/%d %H:%M:%S")
            
            # 3. 強制加上台北時區 (因為資料庫比對邏輯是基於台北時間)
            target_time = target_time_naive.replace(tzinfo=TW_TZ)
            
        except ValueError:
            await interaction.response.send_message("❌ 時間或日期格式錯誤！\n日期格式: YYYY/MM/DD\n時間格式: HH:MM:SS", ephemeral=True)
            return

        # 寫入資料庫
        try:
            with DatabaseSession() as db:
                user = db.query(User).filter(User.discord_id == interaction.user.id).first()
                if not user:
                    user = User(discord_id=interaction.user.id, username=interaction.user.name)
                    db.add(user)
                    db.flush()

                new_schedule = BookingSchedule(
                    user_id=interaction.user.id,
                    train_code=self.train_code,
                    start_station=self.start_st,
                    end_station=self.end_st,
                    train_date=self.train_date, # 這是這班車的出發日期 (爬蟲用)
                    seat_prefer=final_seat_prefer,
                    trigger_time=target_time,   # 這是機器人的啟動時間 (Task檢查用)
                    status="pending"
                )
                db.add(new_schedule)
                db.commit()
                
            # 顯示結果 Embed
            seat_display_map = {"Window": "靠窗", "Aisle": "走道", "None": "不指定"}
            display_seat = seat_display_map.get(final_seat_prefer, "不指定")

            embed = discord.Embed(
                title="✅ 排程已建立！",
                description=(
                    f"目標車次：**{self.train_date}** - **{self.train_code}次**\n"
                    f"座位偏好：**{display_seat}**\n"
                    f"啟動時間：`{target_time.strftime('%Y-%m-%d %H:%M:%S')} (Taipei)`\n\n"
                    "機器人將在指定時間自動執行搶票。"
                ),
                color=discord.Color.green()
            )
            
            view = THSRBackHomeView(self.bot)
            
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ 資料庫寫入失敗: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 資料庫寫入失敗: {e}", ephemeral=True)

class THSRBackHomeView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(THSRHomeButton(bot))

class THSRResultSelect(ui.Select):
    def __init__(self, trains_data):
        options = []
        for t in trains_data[:25]:
            label = f"[{t['id']}] {t['dep']} -> {t['arr']}"
            desc = f"行車: {t['duration']} | {t['discount']}"
            options.append(discord.SelectOption(label=label, description=desc, value=t['id']))

        super().__init__(placeholder="👇 選擇車次以設定「定時搶票」...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_code = self.values[0]
        view = self.view
        
        # 取得日期與座位偏好 (從 QueryView 傳下來的)
        train_date = view.prev_view.date_val 

        await interaction.response.send_modal(
            THSRScheduleModal(
                view.bot, 
                selected_code, 
                view.start_st, 
                view.end_st,
                train_date
            )
        )

class THSRResultView(ui.View):
    def __init__(self, bot, prev_view, driver=None, trains_data=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.prev_view = prev_view 
        self.driver = driver
        self.trains_data = trains_data # 接收資料
        
        self.start_st = prev_view.start_station
        self.end_st = prev_view.end_station

        # 1. 如果有車次資料，加入下拉選單 (供定時搶票用)
        if self.trains_data:
            self.add_item(THSRResultSelect(self.trains_data))

        # 2. 加入翻頁按鈕
        self.add_item(THSRResultEarlierButton())
        self.add_item(THSRResultLaterButton())

    async def on_timeout(self):
        if self.driver:
            self.driver.quit()
    
    @ui.button(label="修改條件", style=discord.ButtonStyle.primary, emoji="🔙", row=2)
    async def back_to_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.driver:
            self.driver.quit()
            self.driver = None
        embed = self.prev_view.get_status_embed()
        await interaction.response.edit_message(embed=embed, view=self.prev_view)

    @ui.button(label="回到主頁", style=discord.ButtonStyle.danger, emoji="🏠", row=2)
    async def back_to_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.driver:
            self.driver.quit()
            self.driver = None
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)