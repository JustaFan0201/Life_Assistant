import re
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from database.models import User, CalendarEvent
from cogs.Itinerary import itinerary_config as conf
class CalendarDatabaseManager:
    def __init__(self, session_factory):
        self.Session = session_factory

        self.tz = conf.TW_TZ

    def add_event(self, user_id: int, event_time: datetime, description: str, is_private: bool, priority: str):
        now = datetime.now(self.tz)
        
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=self.tz)

        if event_time < now:
            return False, "❌ 設定的時間已過，請檢查後重試。"

        with self.Session() as session:
            try:
                user = session.query(User).filter_by(discord_id=user_id).first()
                if not user:
                    user = User(discord_id=user_id, username=f"User_{user_id}")
                    session.add(user)
                    session.flush()

                new_event = CalendarEvent(
                    user_id=user_id,
                    description=description,
                    event_time=event_time,
                    is_private=is_private,
                    priority=priority 
                )
                session.add(new_event)
                session.commit()
                return True, "✅ 行程已成功儲存！"
            except Exception as e:
                session.rollback()
                print(f"[DB Error] add_event: {e}")
                return False, f"寫入失敗: {e}"

    def get_user_events(self, user_id: int):
        with self.Session() as session:
            events = session.query(CalendarEvent)\
                            .filter_by(user_id=user_id)\
                            .order_by(CalendarEvent.event_time.asc())\
                            .all()
            return events

    def delete_event_by_id(self, event_id: int, user_id: int):
        with self.Session() as session:
            event = session.query(CalendarEvent).filter_by(id=event_id, user_id=user_id).first()
            if event:
                session.delete(event)
                session.commit()
                return True, "🗑️ 行程已成功刪除。"
            return False, "❌ 找不到該行程或權限不足。"

    def get_formatted_list(self, user_id: int):
        events = self.get_user_events(user_id)
        formatted = []
        
        for i, ev in enumerate(events, 1):
            time_str = ev.event_time.strftime("%Y-%m-%d %H:%M")
            privacy_emoji = conf.PRIVACY_MAP.get(ev.is_private, "🌍")
            p_emoji = conf.PRIORITY_MAP.get(str(ev.priority), "🟢")
            limit = conf.LIST_DESC_PREVIEW_LEN
            summary = ev.description[:limit] + "..." if len(ev.description) > limit else ev.description
            
            formatted.append({
                "display": f"{privacy_emoji}{p_emoji} #{i} | {time_str} | {summary}",
                "id": ev.id
            })
        return formatted
    
    def get_event_days_for_month(self, user_id: int, year: int, month: int) -> list:
        """回傳指定月份中，有行程的日期清單 (去除重複)"""
        with self.Session() as session:
            # 取得該使用者的所有行程 (簡單過濾，詳細交給 Python 處理以避開 SQLite 複雜的時間語法)
            events = session.query(CalendarEvent).filter_by(user_id=user_id).all()
            
            event_days = set()
            for ev in events:
                if ev.event_time.year == year and ev.event_time.month == month:
                    event_days.add(ev.event_time.day)
            
            return list(event_days)