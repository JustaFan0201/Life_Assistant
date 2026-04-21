from discord.ext import commands,tasks
from datetime import time, datetime
from database.db import SessionLocal
from database.models import TrackerCategory
from cogs.LifeTracker.utils import LifeTracker_Manager, AI_Analyzer
from config import TW_TZ
REPORT_TIME = time(hour=0, minute=0, tzinfo=TW_TZ)

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
