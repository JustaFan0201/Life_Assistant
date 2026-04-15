# cogs/THSR/task.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import asyncio

from database.db import SessionLocal
from database.models import BookingSchedule, THSRProfile, Ticket
from .src.AutoBooking import search_trains, select_train, submit_passenger_info, get_booking_result

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
            with SessionLocal() as db:
                tw_now = datetime.now(TW_TZ)
                now_naive = tw_now.replace(tzinfo=None)

                tasks = db.query(BookingSchedule).filter(
                    BookingSchedule.trigger_time <= now_naive,
                    BookingSchedule.status == "pending"
                ).all()

                for task in tasks:
                    task.status = "processing"
                    
                    # [關鍵修改] 如果是第一次執行，把當下時間寫入 first_executed_at
                    if task.first_executed_at is None:
                        task.first_executed_at = now_naive
                        print(f"🎬 [Task] 任務 ID: {task.id} 首次啟動搶票，寫入 DB: {now_naive}")

                    db.commit()
                    
                    print(f"⏰ [Task] 觸發任務 ID: {task.id} (預定: {task.trigger_time}, 現在: {now_naive})")
                    asyncio.create_task(self.execute_booking(task.id))
                    
        except Exception as e:
            print(f"排程檢查錯誤: {e}")

    @check_schedules.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def execute_booking(self, schedule_id):
        print(f"🚀 [Schedule] 開始執行任務 ID: {schedule_id}")
        driver = None
        task = None
        user_profile = {}
        
        try:
            with SessionLocal() as db:
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
            if status not in ["success", "success_direct"]:
                raise Exception(res_search["msg"])
            
            driver = res_search["driver"]

            # B. 選擇指定車次
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
            await self.handle_retry(schedule_id, error_msg)

        finally:
            if driver: 
                try: driver.quit()
                except: pass

    async def handle_retry(self, schedule_id, error_msg):
        MAX_RETRY_DURATION = timedelta(minutes=30) 
        RETRY_INTERVAL = timedelta(seconds=30)      

        try:
            with SessionLocal() as db:
                task = db.query(BookingSchedule).get(schedule_id)
                if not task: return

                now_naive = datetime.now(TW_TZ).replace(tzinfo=None)
                
                # [關鍵修改] 改為從資料庫讀取 first_executed_at
                # 如果因為某些原因沒讀到，才 fallback 到現在時間 (防呆)
                first_exec_time = task.first_executed_at or now_naive
                elapsed_time = now_naive - first_exec_time

                if elapsed_time < MAX_RETRY_DURATION:
                    next_trigger = now_naive + RETRY_INTERVAL
                    task.trigger_time = next_trigger
                    task.status = "pending" 
                    db.commit()
                    print(f"🔄 [Retry] 任務 ID {schedule_id} 將於 {next_trigger.strftime('%H:%M:%S')} 重試 (已持續搶票: {elapsed_time})")
                else:
                    task.status = "failed"
                    db.commit()
                    print(f"❌ [Timeout] 任務 ID {schedule_id} 已超過 30 分鐘，停止重試。最後錯誤: {error_msg}")
        except Exception as e:
            print(f"處理重試邏輯時發生錯誤: {e}")

    def update_status(self, schedule_id, status):
        with SessionLocal() as db:
            task = db.query(BookingSchedule).get(schedule_id)
            if task:
                task.status = status
                db.commit()

    def save_ticket(self, user_id, res, start, end):
        try:
            with SessionLocal() as db:
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

