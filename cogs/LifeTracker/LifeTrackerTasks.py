from discord.ext import commands, tasks
from datetime import time, datetime
<<<<<<< HEAD
from database.db import SessionLocal
from database.models import TrackerCategory
from cogs.LifeTracker.utils import LifeTracker_Manager, AI_Analyzer
=======
import asyncio
from database import DatabaseSession
from database.models import TrackerCategory, EInvoiceConfig
from cogs.LifeTracker.utils import LifeTracker_Manager,AI_Analyzer
from cogs.LifeTracker.src import InvoicePipeline
>>>>>>> cf7e87d39a1d66fd867e827584aa8bc2aebd9c15
from config import TW_TZ

REPORT_TIME = time(hour=0, minute=0, tzinfo=TW_TZ)
# 🌟 [新增] 設定每日早上 6 點去抓昨日發票
FETCH_INVOICE_TIME = time(hour=6, minute=0, tzinfo=TW_TZ)

class LifeTrackerTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_ai_summary.start()

    @tasks.loop(time=REPORT_TIME)
    async def weekly_ai_summary(self):
        now_tw = datetime.now(TW_TZ)

        if now_tw.weekday() != 0:
            return

        print(f"🚀 [Task] 開始執行每週 AI 總結 (台灣時間: {now_tw})")
        
        try:
            with SessionLocal() as db:
                categories = db.query(TrackerCategory).all()
                
                for cat in categories:
                    analysis_data = LifeTracker_Manager.get_records_for_analysis(cat.id, range_type="week")
                    
                    if analysis_data:
                        try:
                            summary = await AI_Analyzer.analyze_lifestyle(cat.name, analysis_data)
                            
                            cat.last_ai_analysis = summary
                            cat.analysis_updated_at = datetime.now(TW_TZ)
                            db.commit()
                            print(f"✅ 已完成分類 [{cat.name}] 的每週總結")
                        except Exception as e:
                            db.rollback()
                            print(f"❌ 分類 [{cat.name}] 分析失敗: {e}")
        except Exception as e:
            print(f"❌ [Task] 每週總結任務出錯: {e}")

    @tasks.loop(time=FETCH_INVOICE_TIME)
    async def daily_invoice_fetch(self):
        now_tw = datetime.now(TW_TZ)
        print(f"🧾 [Task] 開始執行每日發票自動抓取 (台灣時間: {now_tw})")
        
        try:
            # 撈取所有有設定發票帳號的使用者
            with DatabaseSession() as db:
                configs = db.query(EInvoiceConfig).all()
                # 為了避免資料庫 session 跨非同步操作過期，先將 ID 取出存成 list
                user_ids = [c.user_id for c in configs]
                
            for uid in user_ids:
                print(f"▶️ 正在為 User({uid}) 抓取發票...")
                success, msg = await InvoicePipeline.execute(uid)
                
                if success:
                    print(f"✅ User({uid}) 發票抓取成功。")
                else:
                    print(f"⚠️ User({uid}) 發票抓取失敗: {msg}")
                    
                # 禮貌性延遲：每次抓完一位使用者停頓 10 秒，避免對財政部伺服器造成瞬間 DDoS
                await asyncio.sleep(10)
                
            print(f"🏁 [Task] 每日發票自動抓取任務結束！")
                
        except Exception as e:
            print(f"❌ [Task] 每日發票自動抓取任務出錯: {e}")