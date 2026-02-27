# cogs/THSR/task.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import asyncio

from database.db import DatabaseSession
from database.models import BookingSchedule, THSRProfile, Ticket
from .src.AutoBooking import search_trains, select_train, submit_passenger_info, get_booking_result

# [設定] 手動定義台北時區 (UTC+8)
TW_TZ = timezone(timedelta(hours=8))

class THSRTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_schedules.start()

    def cog_unload(self):
        self.check_schedules.cancel()

    @tasks.loop(seconds=5)
    async def check_schedules(self):
        try:
            with DatabaseSession() as db:
                # 1. 取得現在的台北時間
                tw_now = datetime.now(TW_TZ)
                
                # 2. 轉為 naive 時間 (移除時區標籤)，以便與資料庫的 naive datetime 比對
                now_naive = tw_now.replace(tzinfo=None)

                # 3. 找出「時間到了」且「狀態是 pending」的任務
                tasks = db.query(BookingSchedule).filter(
                    BookingSchedule.trigger_time <= now_naive,
                    BookingSchedule.status == "pending"
                ).all()

                for task in tasks:
                    # 標記為處理中，避免重複執行
                    task.status = "processing"
                    db.commit()
                    
                    print(f"⏰ [Task] 觸發任務 ID: {task.id} (預定: {task.trigger_time}, 現在: {now_naive})")
                    asyncio.create_task(self.execute_booking(task.id))
                    
        except Exception as e:
            print(f"排程檢查錯誤: {e}")

    @check_schedules.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def execute_booking(self, schedule_id):
        """
        真正的搶票邏輯 (Headless 模式)
        包含重試機制：若失敗且未超時，延後再試
        """
        print(f"🚀 [Schedule] 開始執行任務 ID: {schedule_id}")
        driver = None
        task = None
        user_profile = {}
        
        # --- 1. 讀取任務資料 & 使用者個資 ---
        try:
            with DatabaseSession() as db:
                task = db.query(BookingSchedule).get(schedule_id)
                if not task: return

                profile = db.query(THSRProfile).filter(THSRProfile.user_id == task.user_id).first()
                if profile:
                    user_profile = {
                        'pid': profile.personal_id,
                        'phone': profile.phone,
                        'email': profile.email,
                        'tgo': profile.tgo_id
                    }
        except Exception as e:
            print(f"讀取任務資料失敗: {e}")
            return

        if not user_profile.get('pid'):
            print(f"❌ [Schedule] ID {schedule_id} 失敗：無個資")
            self.update_status(schedule_id, "failed")
            return

        # --- 2. 開始執行 Selenium ---
        try:
            # A. 搜尋車次
            res_search = await asyncio.to_thread(
                search_trains,
                task.start_station,
                task.end_station,
                task.train_date,
                "00:00", 
                1,       
                task.seat_prefer,
                task.train_code 
            )

            status = res_search["status"]
            # 如果搜尋失敗 (例如: 查無車次)，拋出異常進入 except 進行重試判斷
            if status not in ["success", "success_direct"]:
                raise Exception(res_search["msg"])
            
            driver = res_search["driver"]

            # B. 選擇指定車次 (非直達才需要)
            if status == "success":
                print("📋 進入列表模式，執行選車...")
                res_select = await asyncio.to_thread(select_train, driver, task.train_code)
                if res_select["status"] != "success":
                    raise Exception(res_select["msg"])
            else:
                print("⚡ 直達個資頁面，跳過選車步驟...")

            # C. 填寫個資
            is_same = (user_profile.get('tgo') and user_profile['tgo'].lower() == 'same')
            tgo_val = None if is_same else user_profile.get('tgo')

            res_submit = await asyncio.to_thread(
                submit_passenger_info,
                driver,
                user_profile['pid'],
                user_profile.get('phone', ''),
                user_profile.get('email', ''),
                tgo_val,
                is_same
            )
            
            if res_submit["status"] != "success":
                raise Exception(res_submit["msg"])

            # D. 取得結果
            final_res = await asyncio.to_thread(get_booking_result, driver)
            
            if final_res["status"] == "success":
                print(f"✅ [Schedule] 訂票成功！代號: {final_res['pnr']}")
                self.save_ticket(task.user_id, final_res, task.start_station, task.end_station)
                self.update_status(schedule_id, "completed")
            else:
                raise Exception(final_res["msg"])

        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ [Schedule] 任務 ID {schedule_id} 執行失敗: {e}")
            
            # [關鍵修改] 呼叫重試處理，而不是直接 failed
            await self.handle_retry(schedule_id, error_msg)

        finally:
            if driver: 
                try: driver.quit()
                except: pass

    async def handle_retry(self, schedule_id, error_msg):
        """
        處理重試邏輯：
        1. 檢查任務建立時間是否超過 30 分鐘
        2. 若未超時 -> 設定下次觸發時間 (現在時間 + 0.5分鐘)，狀態改回 pending
        3. 若已超時 -> 標記為 failed
        """
        MAX_RETRY_DURATION = timedelta(minutes=30) # 最大持續嘗試時間
        RETRY_INTERVAL = timedelta(seconds=30)      # 每次失敗後等待多久再試

        try:
            with DatabaseSession() as db:
                task = db.query(BookingSchedule).get(schedule_id)
                if not task: return

                # 取得現在台北時間 (naive)
                now_naive = datetime.now(TW_TZ).replace(tzinfo=None)
                
                # 計算已耗時 (現在時間 - 任務建立時間)
                elapsed_time = now_naive - task.created_at

                if elapsed_time < MAX_RETRY_DURATION:
                    # [未超時] -> 設定下次重試
                    next_trigger = now_naive + RETRY_INTERVAL
                    task.trigger_time = next_trigger
                    task.status = "pending" # 改回 pending，讓 check_schedules 下次能抓到
                    db.commit()
                    print(f"🔄 [Retry] 任務 ID {schedule_id} 將於 {next_trigger.strftime('%H:%M:%S')} 重試 (已耗時: {elapsed_time})")
                else:
                    # [已超時] -> 標記失敗
                    task.status = "failed"
                    db.commit()
                    print(f"❌ [Timeout] 任務 ID {schedule_id} 已超過 30 分鐘，停止重試。最後錯誤: {error_msg}")
        except Exception as e:
            print(f"處理重試邏輯時發生錯誤: {e}")

    def update_status(self, schedule_id, status):
        """更新任務狀態"""
        with DatabaseSession() as db:
            task = db.query(BookingSchedule).get(schedule_id)
            if task:
                task.status = status
                db.commit()

    def save_ticket(self, user_id, res, start, end):
        """將成功的車票寫入資料庫"""
        try:
            with DatabaseSession() as db:
                ticket = Ticket(
                    user_id=user_id,
                    pnr=res['pnr'],
                    train_date=res['train'].get('date', ''),
                    train_code=res['train'].get('code', ''),
                    departure=res['train'].get('dep_time', ''),
                    arrival=res['train'].get('arr_time', ''),
                    start_station=start,
                    end_station=end,
                    price=res['price'],
                    seats=", ".join(res['seats']),
                    is_paid=False
                )
                db.add(ticket)
                db.commit()
                print(f"💾 車票已存入資料庫 (User: {user_id})")
        except Exception as e:
            print(f"❌ 存票失敗: {e}")
