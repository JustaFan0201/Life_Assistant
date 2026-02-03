import discord
from discord import ui
from datetime import datetime, timedelta

from ...System.ui.buttons import BackToMainButton

from database.db import DatabaseSession
from database.models import User

from .buttons import (
    OpenTHSRQueryButton, 
    OpenTHSRBookingButton,
    OpenTHSRProfileButton,
    THSRSearchButton, 
    THSRBookingSearchButton,
    THSRSwapButton, 
    THSRSeatButton,
    THSRHomeButton
)

from ..src.GetTimeStamp import STATION_MAP

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
                user = db.query(User).filter(User.discord_id == discord_id).first()
                if not user:
                    user = User(discord_id=discord_id, username=username)
                    db.add(user)
                
                user.personal_id = new_data['pid']
                user.phone = new_data['phone']
                user.email = new_data['email']
                user.tgo_id = new_data['tgo']
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
        
        embed.add_field(name="🆔 身分證", value=mask_text(self.user_data.get('pid'), self.is_hidden), inline=True)
        embed.add_field(name="📱 手機", value=mask_text(self.user_data.get('phone'), self.is_hidden), inline=True)
        embed.add_field(name="📧 信箱", value=mask_text(self.user_data.get('email'), self.is_hidden), inline=False)
        embed.add_field(name="💎 TGo", value=self.user_data.get('tgo') if self.user_data.get('tgo') else "未設定", inline=True)
        
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
            value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次\n🎫 **自動購票**：自動化搶票系統\n📝 **設定資料**：預存身分證與聯絡資訊", 
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

# 2. 高鐵全功能查詢介面 (Query View)
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
        await interaction.response.edit_message(embed=embed, view=self.prev_view)

    @ui.button(label="回高鐵主頁", style=discord.ButtonStyle.danger, emoji="🏠")
    async def back_to_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 4. 自動訂票介面 (Booking View)
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

class THSRTrainSelect(ui.Select):
    def __init__(self, trains):
        options = []
        # 限制顯示前 25 筆 (Discord 上限)
        for t in trains[:25]: 
            # 處理優惠顯示
            discount_icon = ""
            raw_discount = t.get('discount', '')
            if "早鳥" in raw_discount: discount_icon = "🦅"
            elif "大學生" in raw_discount: discount_icon = "🎓"
            
            label = f"[{t['code']}] {t['departure']} ➜ {t['arrival']}"
            desc = f"⏱️ {t['duration']} {discount_icon} {raw_discount}"
            
            # 確保描述不超過長度
            if len(desc) > 100: desc = desc[:97] + "..."
            
            options.append(discord.SelectOption(label=label, description=desc, value=t['code']))
        
        super().__init__(placeholder="👇 請選擇一班列車...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_code = self.values[0]
        # ★ 這裡需要 import Modal，使用區域引用避免循環 ★
        from .buttons import THSRPassengerModal
        await interaction.response.send_modal(THSRPassengerModal(self.view.bot, self.view.driver, selected_code))

class THSRTrainSelectView(ui.View):
    def __init__(self, bot, driver, trains):
        super().__init__(timeout=None)
        self.bot = bot
        self.driver = driver
        self.trains = trains
        # 加入下拉選單
        self.add_item(THSRTrainSelect(trains))

    @staticmethod
    def create_train_selection_ui(bot, driver, trains):
        """
        [工廠方法] 產生選擇車次的 Embed 與 View
        """
        # 1. 建立 Embed
        embed = discord.Embed(
            title="🚄 請選擇車次 (自動訂票)", 
            description=f"✅ 已為您找到 **{len(trains)}** 班列車\n請在下方選單選擇，或查看詳細資訊：",
            color=discord.Color.green()
        )
        
        # 2. 填充車次資訊 (最多顯示 10 筆，避免 Embed 太長)
        for t in trains[:10]:
            # 美化優惠資訊
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

        # 3. 建立 View
        view = THSRTrainSelectView(bot, driver, trains)
        
        return embed, view

    @ui.button(label="取消訂票 (返回設定)", style=discord.ButtonStyle.danger, row=4)
    async def cancel_booking(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        # 1. 關閉瀏覽器
        if self.driver:
            self.driver.quit()
            
        # 2. 返回 THSRBookingView (訂票設定頁面)
        # 使用區域引用
        from .view import THSRBookingView
        embed, view = THSRBookingView.create_new_ui(self.bot)
        
        # 提示使用者已取消
        embed.description = "❌ 上一次訂票已取消，請重新設定條件。"
        embed.color = discord.Color.red()
        
        await interaction.edit_original_response(embed=embed, view=view)

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