import discord
from discord import ui
import asyncio

# 引入爬蟲與自動化邏輯
from ..src.GetTimeStamp import get_thsr_schedule
from ..src.AutoBooking import search_trains, select_train, submit_passenger_info, get_booking_result

# [Dashboard] 開啟查詢按鈕
class OpenTHSRQueryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="查詢時刻表", style=discord.ButtonStyle.primary, emoji="🗓️", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from .view import THSRQueryView
        embed, view = THSRQueryView.create_new_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# [Dashboard] 開啟訂票按鈕
class OpenTHSRBookingButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="自動訂票", style=discord.ButtonStyle.success, emoji="🎫", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from .view import THSRBookingView
        embed, view = THSRBookingView.create_new_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 1. 一般查詢執行按鈕
class THSRSearchButton(ui.Button):
    def __init__(self):
        super().__init__(label="查詢", style=discord.ButtonStyle.success, row=4, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view = self.view 
        await interaction.response.defer()
        
        ticket_info = (
            f"> 🚄 **起訖**：`{view.start_station}` ➔ `{view.end_station}`\n"
            f"> 📅 **時間**：`{view.date_val}` 　⏰ `{view.time_val}`\n"
            f"> 🎫 **設定**：`{view.trip_type}` ／ `{view.ticket_type}`"
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
                view.start_station, 
                view.end_station, 
                view.date_val, 
                view.time_val,
                view.ticket_type,
                view.trip_type
            )
            
            if isinstance(result_data, dict) and "data" in result_data:
                final_embed = discord.Embed(
                    title=f"🚄 {result_data['start']} ➔ {result_data['end']}",
                    description=f"📅 **{result_data['date']}** ({view.time_val} 後)\n🎫 {view.trip_type} / {view.ticket_type}",
                    color=0xec6c00
                )
                
                if not result_data['data']:
                     final_embed.description += "\n⚠️ 查無班次"
                else:
                    for train in result_data['data']:
                        # --- 這裡加入優惠顯示邏輯 ---
                        dep = train['dep']
                        arr = train['arr']
                        duration = train['duration']
                        discount = train.get('discount', '無優惠')
                        
                        # 簡單美化
                        if "早鳥" in discount:
                            discount_display = f"🦅 **{discount}**"
                        elif "大學生" in discount:
                            discount_display = f"🎓 **{discount}**"
                        elif discount == "無優惠" or not discount:
                            discount_display = "🏷️ 原價"
                        else:
                            discount_display = f"🏷️ {discount}"

                        val = f"`{dep} ➔ {arr}`\n⏱️ {duration} | {discount_display}"
                        final_embed.add_field(name=f"🚅 {train['id']}", value=val, inline=True)
                
                # 呼叫結果頁面 View
                from .view import THSRResultView
                await interaction.edit_original_response(embed=final_embed, view=THSRResultView(view.bot, view))

            else:
                # 查詢失敗 (邏輯錯誤)
                from .view import THSRErrorView
                err_embed, err_view = THSRErrorView.create_error_ui(view.bot, "查詢失敗", str(result_data.get('error')))
                await interaction.edit_original_response(embed=err_embed, view=err_view)
            
        except Exception as e:
            # 系統報錯
            print(f"Error: {e}")
            from .view import THSRErrorView
            err_embed, err_view = THSRErrorView.create_error_ui(view.bot, "系統發生錯誤", str(e))
            await interaction.edit_original_response(embed=err_embed, view=err_view)

# 2. 自動訂票執行按鈕
class THSRBookingSearchButton(ui.Button):
    def __init__(self):
        super().__init__(label="開始訂票", style=discord.ButtonStyle.success, emoji="🚀", row=4, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view = self.view 
        user = interaction.user
        await interaction.response.defer()

        # Log
        print(f"🚀 [訂票啟動] User: {user.name} | {view.start_station}->{view.end_station}")

        loading_embed = discord.Embed(
            title="🎫 正在啟動自動訂票...", 
            description=f"👤 **操作者**: {user.mention}\n🚄 **{view.start_station}** ➔ **{view.end_station}**\n📅 **{view.date_val}** ({view.time_val})\n💺 **座位偏好**: {view.seat_prefer}\n\n⏳ **正在開啟瀏覽器並破解驗證碼...**", 
            color=discord.Color.green()
        )
        if user.avatar:
            loading_embed.set_footer(text=f"Requested by {user.display_name}", icon_url=user.avatar.url)

        await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            # 執行搜尋
            result = await asyncio.to_thread(
                search_trains,
                view.start_station,
                view.end_station,
                view.date_val,
                view.time_val,
                1, 
                view.seat_prefer
            )

            if result["status"] == "success":
                driver = result["driver"]
                trains = result["trains"]
                
                # ★★★ 關鍵修改：使用工廠方法取得 Embed 和 View ★★★
                from .view import THSRTrainSelectView
                embed, select_view = THSRTrainSelectView.create_train_selection_ui(view.bot, driver, trains)
                
                await interaction.edit_original_response(embed=embed, view=select_view)
            else:
                from .view import THSRErrorView
                embed, view = THSRErrorView.create_error_ui(view.bot, "訂票啟動失敗", result["msg"])
                await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            from .view import THSRErrorView
            embed, view = THSRErrorView.create_error_ui(view.bot, "瀏覽器啟動錯誤", str(e))
            await interaction.edit_original_response(embed=embed, view=view)

# 3. 交換按鈕
class THSRSwapButton(ui.Button):
    def __init__(self):
        super().__init__(emoji="🔁", style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        self.view.start_station, self.view.end_station = self.view.end_station, self.view.start_station
        await self.view.refresh_ui(interaction)

# 4. 座位偏好按鈕
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

# 5. 回主頁按鈕
class THSRHomeButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="主頁", style=discord.ButtonStyle.danger, row=4)
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        from .view import THSR_DashboardView
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 6. 選擇車次後填寫乘客資料的 Modal
class THSRPassengerModal(ui.Modal, title="填寫取票資訊"):
    pid = ui.TextInput(label="身分證字號", placeholder="必填 (例如 A123456789)", min_length=10, max_length=10)
    phone = ui.TextInput(label="手機號碼", placeholder="選填 (09xxxxxxxx)", required=False, max_length=10)
    email = ui.TextInput(label="電子郵件", placeholder="選填 (用於接收通知)", required=False)
    tgo_id = ui.TextInput(label="TGo 會員帳號", placeholder="選填 (填寫 same 代表同身分證)", required=False)

    def __init__(self, bot, driver, train_code):
        super().__init__()
        self.bot = bot
        self.driver = driver
        self.train_code = train_code

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        progress_embed = discord.Embed(title="🔄 正在執行訂票...", description=f"您選擇了車次 **{self.train_code}**\n系統正在自動填寫資料並送出，請勿關閉...", color=discord.Color.gold())
        await interaction.edit_original_response(embed=progress_embed, view=None)

        try:
            select_res = await asyncio.to_thread(select_train, self.driver, self.train_code)
            if select_res["status"] != "success": raise Exception(select_res["msg"])

            is_same_pid = False
            tgo_val = self.tgo_id.value
            if tgo_val and (tgo_val.lower() == "same" or tgo_val == "同"):
                is_same_pid = True
                tgo_val = None

            submit_res = await asyncio.to_thread(
                submit_passenger_info, 
                self.driver, 
                self.pid.value, 
                self.phone.value, 
                self.email.value, 
                tgo_val,
                is_same_pid
            )

            if submit_res["status"] == "success":
                final_result = await asyncio.to_thread(get_booking_result, self.driver)
                
                if final_result["status"] == "success":
                    success_embed = discord.Embed(title="🎉 訂位成功！", color=discord.Color.green())
                    success_embed.add_field(name="訂位代號", value=f"`{final_result['pnr']}`", inline=False)
                    success_embed.add_field(name="總金額", value=final_result['price'], inline=True)
                    success_embed.add_field(name="狀態", value=final_result['payment_status'], inline=True)
                    
                    train_str = f"{final_result['train'].get('code')} ({final_result['train'].get('date')})\n{final_result['train'].get('dep_time')} ➔ {final_result['train'].get('arr_time')}"
                    success_embed.add_field(name="車次資訊", value=train_str, inline=False)
                    success_embed.add_field(name="座位", value=", ".join(final_result['seats']), inline=False)
                    success_embed.set_footer(text="請記得前往高鐵官網或 App 付款")
                    
                    # 成功後也提供一個回主頁按鈕 (選用)
                    from .view import THSRErrorView 
                    # 這裡直接實例化 View 只為了拿 Home 按鈕
                    view = THSRErrorView(self.bot)
                    await interaction.edit_original_response(embed=success_embed, view=view)
                else:
                    # 訂位成功但抓不到資料
                    from .view import THSRErrorView
                    err_embed, err_view = THSRErrorView.create_error_ui(self.bot, "擷取結果失敗", f"訂位可能已完成，但無法讀取細節：{final_result['msg']}")
                    await interaction.edit_original_response(embed=err_embed, view=err_view)
            else:
                # 個資填寫失敗
                from .view import THSRErrorView
                err_embed, err_view = THSRErrorView.create_error_ui(self.bot, "個資填寫失敗", submit_res['msg'])
                await interaction.edit_original_response(embed=err_embed, view=err_view)

        except Exception as e:
            # 流程中斷錯誤
            from .view import THSRErrorView
            err_embed, err_view = THSRErrorView.create_error_ui(self.bot, "訂票流程錯誤", str(e))
            await interaction.edit_original_response(embed=err_embed, view=err_view)
        
        finally:
            if self.driver: self.driver.quit()