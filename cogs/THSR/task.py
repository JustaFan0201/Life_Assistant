# cogs/THSR/task.py
import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio

from database.db import DatabaseSession
from database.models import BookingSchedule, THSRProfile, Ticket
# 引入你的搶票邏輯
from .src.AutoBooking import search_trains, select_train, submit_passenger_info, get_booking_result

class THSRTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_schedules.start() # 啟動迴圈

    def cog_unload(self):
        self.check_schedules.cancel()

    @tasks.loop(seconds=5) # 每 5 秒檢查一次
    async def check_schedules(self):
        try:
            with DatabaseSession() as db:
                now = datetime.now()
                # 找出「時間到了」且「狀態是 pending」的任務
                tasks = db.query(BookingSchedule).filter(
                    BookingSchedule.trigger_time <= now,
                    BookingSchedule.status == "pending"
                ).all()

                for task in tasks:
                    # 1. 標記為處理中，避免重複執行
                    task.status = "processing"
                    db.commit()
                    
                    # 2. 啟動非同步執行
                    asyncio.create_task(self.execute_booking(task.id))
                    
        except Exception as e:
            print(f"排程檢查錯誤: {e}")

    @check_schedules.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def execute_booking(self, schedule_id):
        """
        真正的搶票邏輯 (Headless 模式)
        """
        print(f"🚀 [Schedule] 開始執行任務 ID: {schedule_id}")
        driver = None
        
        # 1. 讀取任務資料 & 使用者個資
        task = None
        user_profile = {}
        
        try:
            with DatabaseSession() as db:
                task = db.query(BookingSchedule).get(schedule_id)
                if not task: return

                # 讀取個資
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

            # 檢查回傳狀態
            status = res_search["status"]
            if status not in ["success", "success_direct"]:
                raise Exception(res_search["msg"])
            
            driver = res_search["driver"]

            # B. 選擇指定車次 (只有在非直達的情況下才需要選)
            if status == "success":
                print("📋 進入列表模式，執行選車...")
                res_select = await asyncio.to_thread(select_train, driver, task.train_code)
                if res_select["status"] != "success":
                    raise Exception(res_select["msg"])
            else:
                print("⚡ 直達個資頁面，跳過選車步驟...")

            # C. 填寫個資 (後續流程完全一樣)
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
                # 成功！寫入 Ticket 資料庫
                self.save_ticket(task.user_id, final_res, task.start_station, task.end_station)
                self.update_status(schedule_id, "completed")
            else:
                raise Exception(final_res["msg"])

        except Exception as e:
            print(f"❌ [Schedule] 任務 ID {schedule_id} 執行失敗: {e}")
            self.update_status(schedule_id, "failed")

        finally:
            if driver: driver.quit()

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
                    is_paid=False # 剛訂好通常是未付款
                )
                db.add(ticket)
                db.commit()
                print(f"💾 車票已存入資料庫 (User: {user_id})")
        except Exception as e:
            print(f"❌ 存票失敗: {e}")

async def setup(bot):
    await bot.add_cog(THSRTask(bot))