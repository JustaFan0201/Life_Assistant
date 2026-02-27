# cogs/THSR/ui/buttons.py
import discord
from discord import ui
import asyncio

from database.db import DatabaseSession
from database.models import User, THSRProfile, Ticket,BookingSchedule

from ..src.GetTimeStamp import get_thsr_schedule, load_more_schedule
from ..src.AutoBooking import search_trains, select_train, submit_passenger_info, get_booking_result, load_new_trains

def check_user_profile(user_id):
    """檢查使用者是否已設定身分證"""
    try:
        with DatabaseSession() as db:
            profile = db.query(THSRProfile).filter(THSRProfile.user_id == user_id).first()
            if profile and profile.personal_id:
                return True
    except Exception as e:
        print(f"資料庫檢查錯誤: {e}")
    return False

async def show_profile_missing_error(interaction, bot):
    """顯示未設定個資的錯誤訊息"""
    embed = discord.Embed(
        title="❌ 無法使用此功能",
        description="您尚未設定 **身分證字號**，無法進行查詢或訂票。\n請先點擊下方按鈕設定個人資料。",
        color=discord.Color.red()
    )
    from .view import THSR_DashboardView
    
    dash_embed, dash_view = THSR_DashboardView.create_dashboard_ui(bot)
    
    await interaction.response.edit_message(embed=embed, view=dash_view)

async def _common_schedule_paging(interaction: discord.Interaction, button: ui.Button, direction: str):
    """一般查詢結果的翻頁邏輯"""
    view = button.view
    if not view.driver:
        await interaction.response.send_message("❌ 瀏覽器已關閉，請重新查詢", ephemeral=True)
        return

    await interaction.response.defer()
    
    result = await asyncio.to_thread(load_more_schedule, view.driver, direction)
    
    if result["status"] == "success":
        data_list = result["data"] # 新的車次列表
        query_view = view.prev_view # 取得原本的查詢條件 View
        
        # 建立新的 Embed
        final_embed = discord.Embed(
            title=f"🚄 {query_view.start_station} ➔ {query_view.end_station}",
            description=f"📅 {query_view.date_val} (翻頁結果)\n🎫 {query_view.trip_type} / {query_view.ticket_type}",
            color=0xec6c00
        )
        
        for train in data_list:
            discount = train['discount']
            if "早鳥" in discount: d_display = f"🦅 **{discount}**"
            elif "大學生" in discount: d_display = f"🎓 **{discount}**"
            elif discount == "無優惠": d_display = "🏷️ 原價"
            else: d_display = f"🏷️ {discount}"

            val = f"`{train['dep']} ➔ {train['arr']}`\n⏱️ {train['duration']} | {d_display}"
            final_embed.add_field(name=f"🚅 {train['id']}", value=val, inline=False)
            
        # 重新建立 View (傳入新的 data_list 以更新下拉選單)
        from .view import THSRResultView
        new_view = THSRResultView(view.bot, query_view, view.driver, data_list)
        
        await interaction.edit_original_response(embed=final_embed, view=new_view)
        
    else:
        await interaction.followup.send(f"⚠️ {result['msg']}", ephemeral=True)

async def _common_load_more_handler(interaction: discord.Interaction, button: ui.Button, direction: str):
    """自動訂票選車頁面的翻頁邏輯"""
    view = button.view
    await interaction.response.defer()
    
    result = await asyncio.to_thread(load_new_trains, view.driver, direction)
    
    if result["status"] == "success":
        new_trains = result["trains"]
        if not new_trains:
            await interaction.followup.send("⚠️ 載入成功但列表為空 (可能無車次)", ephemeral=True)
            return

        from .view import THSRTrainSelectView
        embed, new_view = THSRTrainSelectView.create_train_selection_ui(
            view.bot, view.driver, new_trains, view.start_st, view.end_st
        )
        await interaction.edit_original_response(embed=embed, view=new_view)
    else:
        await interaction.followup.send(f"⚠️ {result['msg']}", ephemeral=True)

async def run_booking_flow(interaction: discord.Interaction, bot, driver, train_code, user_data, start_st=None, end_st=None):
    """執行自動訂票流程：選車次(視情況) -> 填個資 -> 取得結果"""
    if not interaction.response.is_done():
        await interaction.response.defer()
        
    progress_embed = discord.Embed(
        title="🔄 正在執行訂票...", 
        description=f"您選擇了車次 **{train_code}**\n正在使用您的個人資料自動下單，請勿關閉...", 
        color=discord.Color.gold()
    )
    await interaction.edit_original_response(embed=progress_embed, view=None)

    try:
        current_url = driver.current_url
        page_source = driver.page_source
        
        # 情況 1: 已經在選車頁面 (TrainSelection) -> 執行 select_train
        if "TrainSelection" in current_url:
            select_res = await asyncio.to_thread(select_train, driver, train_code)
            if select_res["status"] != "success": 
                raise Exception(select_res["msg"])
        
        # 情況 2: 已經在個資頁面 (BookingS2Form) -> 跳過 select_train
        elif "BookingS2Form" in current_url or "idNumber" in page_source:
            pass # 直達
            
        else:
            print("⚠️ [BookingFlow] 頁面狀態不明，嘗試盲選車次...")
            select_res = await asyncio.to_thread(select_train, driver, train_code)
            # [修改] 改用 status 來判斷，而不是依賴 except
            if select_res["status"] != "success":
                raise Exception(f"車次選擇失敗: {select_res['msg']}")

        # 處理個資
        pid = user_data.get('pid')
        phone = user_data.get('phone')
        email = user_data.get('email')
        tgo = user_data.get('tgo')
        is_same_pid = False
        if tgo and (tgo.lower() == "same" or tgo == "同"):
            is_same_pid = True
            tgo = None

        # 填寫個資
        submit_res = await asyncio.to_thread(submit_passenger_info, driver, pid, phone, email, tgo, is_same_pid)

        if submit_res["status"] == "success":
            final_result = await asyncio.to_thread(get_booking_result, driver)
            
            if final_result["status"] == "success":
                # 寫入資料庫
                try:
                    with DatabaseSession() as db:
                        ticket = Ticket(
                            user_id=interaction.user.id,
                            pnr=final_result['pnr'],
                            train_date=final_result['train'].get('date'),
                            train_code=final_result['train'].get('code'),
                            departure=final_result['train'].get('dep_time'),
                            arrival=final_result['train'].get('arr_time'),
                            start_station=start_st,
                            end_station=end_st,
                            price=final_result['price'],
                            seats=", ".join(final_result['seats']),
                            is_paid=False
                        )
                        db.add(ticket)
                        db.commit()
                        print(f"✅ [Database] 訂票紀錄已儲存: {final_result['pnr']}")
                except Exception as db_e:
                    print(f"❌ [Database] 訂票紀錄寫入失敗: {db_e}")
                
                from .view import THSRSuccessView
                embed, view = THSRSuccessView.create_booking_success_ui(bot, final_result, start_st, end_st)
                await interaction.edit_original_response(embed=embed, view=view)
                
            else:
                from .view import THSRErrorView
                embed, view = THSRErrorView.create_error_ui(bot, "擷取結果失敗", final_result['msg'])
                await interaction.edit_original_response(embed=embed, view=view)
        else:
            from .view import THSRErrorView
            embed, view = THSRErrorView.create_error_ui(bot, "個資填寫失敗", submit_res['msg'])
            await interaction.edit_original_response(embed=embed, view=view)

    except Exception as e:
        from .view import THSRErrorView
        embed, view = THSRErrorView.create_error_ui(bot, "訂票流程錯誤", str(e))
        await interaction.edit_original_response(embed=embed, view=view)
    
    finally:
        if driver: 
            try: driver.quit()
            except: pass

# 1. 查詢結果翻頁按鈕 (一般查詢)
class THSRResultEarlierButton(ui.Button):
    def __init__(self):
        super().__init__(label="較早班次", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
    async def callback(self, interaction: discord.Interaction):
        await _common_schedule_paging(interaction, self, "earlier")

class THSRResultLaterButton(ui.Button):
    def __init__(self):
        super().__init__(label="較晚班次", style=discord.ButtonStyle.secondary, emoji="➡️", row=1)
    async def callback(self, interaction: discord.Interaction):
        await _common_schedule_paging(interaction, self, "later")

# 2. 自動訂票選車翻頁按鈕
class THSRLoadEarlierButton(ui.Button):
    def __init__(self):
        super().__init__(label="更早車次", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
    async def callback(self, interaction: discord.Interaction):
        await _common_load_more_handler(interaction, self, "earlier")

class THSRLoadLaterButton(ui.Button):
    def __init__(self):
        super().__init__(label="更晚車次", style=discord.ButtonStyle.secondary, emoji="➡️", row=1)
    async def callback(self, interaction: discord.Interaction):
        await _common_load_more_handler(interaction, self, "later")

# 3. [Dashboard] 開啟選單按鈕
class OpenTHSRQueryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="定時訂票", style=discord.ButtonStyle.success, emoji="🗓️", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 1. 檢查身分證
        if not check_user_profile(interaction.user.id):
            await show_profile_missing_error(interaction, self.bot)
            return

        # 2. 通過檢查，進入查詢頁面
        from .view import THSRQueryView
        embed, view = THSRQueryView.create_new_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

class OpenTHSRBookingButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="線上訂票", style=discord.ButtonStyle.success, emoji="🎫", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 1. 檢查身分證
        if not check_user_profile(interaction.user.id):
            await show_profile_missing_error(interaction, self.bot)
            return

        # 2. 通過檢查，進入訂票頁面
        from .view import THSRBookingView
        embed, view = THSRBookingView.create_new_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

class OpenTHSRProfileButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="設定個資", style=discord.ButtonStyle.primary, emoji="📝", row=2)
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        user_data = {}
        try:
            with DatabaseSession() as db:
                profile = db.query(THSRProfile).filter(THSRProfile.user_id == interaction.user.id).first()
                if profile:
                    user_data = {'pid': profile.personal_id, 'phone': profile.phone, 'email': profile.email, 'tgo': profile.tgo_id}
        except: pass
        from .view import THSRProfileView
        view = THSRProfileView(self.bot, user_data)
        await interaction.response.edit_message(embed=view.generate_embed(), view=view)

class OpenTHSRTicketsButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="我的車票", style=discord.ButtonStyle.primary, emoji="📂", row=2)
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        tickets = []
        try:
            with DatabaseSession() as db:
                tickets = db.query(Ticket).filter(Ticket.user_id == interaction.user.id).order_by(Ticket.created_at.desc()).limit(10).all()
        except:
            await interaction.followup.send("❌ 資料庫讀取失敗", ephemeral=True)
            return
        from .view import THSRTicketListView
        embed, view = THSRTicketListView.create_ticket_ui(self.bot, tickets)
        await interaction.edit_original_response(embed=embed, view=view)

class ToggleScheduleButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="查看定時任務", style=discord.ButtonStyle.secondary, emoji="⏳", row=0)
        self.bot = bot
        
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        schedules = []
        try:
            with DatabaseSession() as db:
                # 撈取該使用者的定時任務，依照建立時間倒序排列
                schedules = db.query(BookingSchedule).filter(
                    BookingSchedule.user_id == interaction.user.id
                ).order_by(BookingSchedule.created_at.desc()).limit(10).all()
        except Exception as e:
            print(f"查詢任務失敗: {e}")
            await interaction.followup.send("❌ 資料庫讀取失敗", ephemeral=True)
            return

        from .view import THSRScheduleListView
        embed, view = THSRScheduleListView.create_schedule_ui(self.bot, schedules)
        await interaction.edit_original_response(embed=embed, view=view)

class ToggleTicketsButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="查看已訂車票", style=discord.ButtonStyle.secondary, emoji="🎫", row=0)
        self.bot = bot
        
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        tickets = []
        try:
            with DatabaseSession() as db:
                # 撈取該使用者的實體車票
                tickets = db.query(Ticket).filter(
                    Ticket.user_id == interaction.user.id
                ).order_by(Ticket.created_at.desc()).limit(10).all()
        except Exception as e:
            print(f"查詢車票失敗: {e}")
            await interaction.followup.send("❌ 資料庫讀取失敗", ephemeral=True)
            return
            
        from .view import THSRTicketListView
        embed, view = THSRTicketListView.create_ticket_ui(self.bot, tickets)
        await interaction.edit_original_response(embed=embed, view=view)

# 4. 功能按鈕 (交換、座位、主頁)
class THSRSwapButton(ui.Button):
    def __init__(self):
        super().__init__(emoji="🔁", style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        self.view.start_station, self.view.end_station = self.view.end_station, self.view.start_station
        await self.view.refresh_ui(interaction)

class THSRSeatButton(ui.Button):
    def __init__(self, current_seat="None"):
        label_map = {"None": "座位: 無", "Window": "座位: 靠窗", "Aisle": "座位: 走道"}
        super().__init__(label=label_map.get(current_seat, "座位: 無"), style=discord.ButtonStyle.primary, row=4)
    async def callback(self, interaction: discord.Interaction):
        states = ["None", "Window", "Aisle"]
        current_idx = states.index(self.view.seat_prefer)
        self.view.seat_prefer = states[(current_idx + 1) % 3]
        label_map = {"None": "座位: 無", "Window": "座位: 靠窗", "Aisle": "座位: 走道"}
        self.label = label_map[self.view.seat_prefer]
        await self.view.refresh_ui(interaction)

class THSRHomeButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="主頁", style=discord.ButtonStyle.danger, row=4)
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        from .view import THSR_DashboardView
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 5. ★★★ 查詢執行按鈕 (THSRSearchButton) ★★★
class THSRSearchButton(ui.Button):
    def __init__(self):
        super().__init__(label="查詢", style=discord.ButtonStyle.success, row=4, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view = self.view 
        await interaction.response.defer()
        
        ticket_info = (
            f"🚄 **起訖**：`{view.start_station}` ➔ `{view.end_station}`\n"
            f"📅 **時間**：`{view.date_val}` 　⏰ `{view.time_val}`\n"
            f"🎫 **設定**：`{view.trip_type}` ／ `{view.ticket_type}`"
        )
        loading_embed = discord.Embed(
            title="🔍 正在搜尋班次...", 
            description=f"{ticket_info}\n\n⏳ **正在連線至高鐵官網擷取資料，請稍候...**", 
            color=discord.Color.from_rgb(0, 162, 232)
        )
        await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            result_data = await asyncio.to_thread(
                get_thsr_schedule, 
                view.start_station, view.end_station, view.date_val, 
                view.time_val, view.ticket_type, view.trip_type
            )
            
            if isinstance(result_data, dict) and "data" in result_data:
                driver = result_data.get("driver")
                trains_data = result_data.get("data")

                final_embed = discord.Embed(
                    title=f"🚄 {result_data['start']} ➔ {result_data['end']}",
                    description=f"📅 **{result_data['date']}** ({view.time_val} 後)\n🎫 {view.trip_type} / {view.ticket_type}",
                    color=0xec6c00
                )
                
                if not trains_data:
                    final_embed.description += "\n⚠️ 查無班次"
                else:
                    for train in trains_data:
                        discount = train.get('discount', '無優惠')
                        if "早鳥" in discount: d_disp = f"🦅 **{discount}**"
                        elif "大學生" in discount: d_disp = f"🎓 **{discount}**"
                        elif discount == "無優惠" or not discount: d_disp = "🏷️ 原價"
                        else: d_disp = f"🏷️ {discount}"

                        val = f"`{train['dep']} ➔ {train['arr']}`\n⏱️ {train['duration']} | {d_disp}"
                        final_embed.add_field(name=f"🚅 {train['id']}", value=val, inline=False)
                
                from .view import THSRResultView
                result_view = THSRResultView(view.bot, view, driver, trains_data)
                
                await interaction.edit_original_response(embed=final_embed, view=result_view)

            else:
                from .view import THSRErrorView
                embed, view = THSRErrorView.create_error_ui(view.bot, "查詢失敗", str(result_data.get('error')))
                await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            from .view import THSRErrorView
            embed, view = THSRErrorView.create_error_ui(view.bot, "系統發生錯誤", str(e))
            await interaction.edit_original_response(embed=embed, view=view)

# 6. 自動訂票搜尋按鈕 (THSRBookingSearchButton)
class THSRBookingSearchButton(ui.Button):
    def __init__(self):
        super().__init__(label="開始訂票", style=discord.ButtonStyle.success, emoji="🚀", row=4, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view = self.view 
        user = interaction.user
        await interaction.response.defer()

        loading_embed = discord.Embed(
            title="🎫 正在啟動自動訂票...", 
            description=f"👤 **操作者**: {user.mention}\n🚄 **{view.start_station}** ➔ **{view.end_station}**\n📅 **{view.date_val}** ({view.time_val})\n💺 **座位偏好**: {view.seat_prefer}\n\n⏳ **正在開啟瀏覽器並破解驗證碼...**", 
            color=discord.Color.green()
        )
        await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            result = await asyncio.to_thread(
                search_trains,
                view.start_station, view.end_station, view.date_val, 
                view.time_val, 1, view.seat_prefer
            )

            if result["status"] == "success":
                from .view import THSRTrainSelectView
                embed, select_view = THSRTrainSelectView.create_train_selection_ui(
                    view.bot, result["driver"], result["trains"], 
                    view.start_station, view.end_station
                )
                await interaction.edit_original_response(embed=embed, view=select_view)
            else:
                from .view import THSRErrorView
                embed, view = THSRErrorView.create_error_ui(view.bot, "訂票啟動失敗", result["msg"])
                await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            from .view import THSRErrorView
            embed, view = THSRErrorView.create_error_ui(view.bot, "瀏覽器啟動錯誤", str(e))
            await interaction.edit_original_response(embed=embed, view=view)