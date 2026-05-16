from datetime import datetime
from database.models import CalendarEvent
from database.db_utils import with_db_decorator, get_user
from cogs.Itinerary import itinerary_config as conf
from config import TW_TZ


class CalendarDatabaseManager:
    def __init__(self, session_factory):
        self.session = session_factory

    @staticmethod
    @with_db_decorator
    def add_event(user_id: int, user_name: str, event_time: datetime, description: str, is_private: bool, db=None):
        now_tw = datetime.now(TW_TZ).replace(tzinfo=None)
        
        if event_time.tzinfo is not None:
            event_time = event_time.astimezone(TW_TZ).replace(tzinfo=None)

        if event_time < now_tw:
            return False, f'❌ 設定的時間 {event_time.strftime("%Y-%m-%d %H:%M")} 已過，請檢查後重試。'

        user = get_user(discord_id=user_id, user_name=user_name, db=db)
        
        new_event = CalendarEvent(
            user_id=user.discord_id,
            description=description,
            event_time=event_time, 
            is_private=is_private
        )
        db.add(new_event)
        db.commit()
        return True, "✅ 行程已成功儲存！"

    @staticmethod
    @with_db_decorator
    def get_user_events(user_id: int, db=None):
        events = db.query(CalendarEvent)\
                    .filter_by(user_id=user_id)\
                    .order_by(CalendarEvent.event_time.asc())\
                    .all()
        return events

    @staticmethod
    @with_db_decorator
    def delete_event_by_id(event_id: int, user_id: int, db=None):
        event = db.query(CalendarEvent).filter_by(id=event_id, user_id=user_id).first()
        if event:
            db.delete(event)
            db.commit()
            return True, "🗑️ 行程已成功刪除。"
        return False, "❌ 找不到該行程或權限不足。"

    @staticmethod
    def get_formatted_list(user_id: int):
        events = CalendarDatabaseManager.get_user_events(user_id)
        formatted = []
        
        for i, ev in enumerate(events, 1):
            time_str = ev.event_time.strftime("%Y-%m-%d %H:%M")
            privacy_emoji = conf.PRIVACY_MAP.get(ev.is_private, "🌍")
            
            limit = conf.LIST_DESC_PREVIEW_LEN
            summary = ev.description[:limit] + "..." if len(ev.description) > limit else ev.description
            
            formatted.append({
                "display": f"{privacy_emoji} #{i} | {time_str} | {summary}",
                "id": ev.id
            })
        return formatted
    
    def get_event_days_for_month(self, user_id: int, year: int, month: int) -> list:
        """回傳指定月份中，有行程的日期清單 (去除重複)"""
        with self.session() as session:
            # 取得該使用者的所有行程 (簡單過濾，詳細交給 Python 處理以避開 SQLite 複雜的時間語法)
            events = session.query(CalendarEvent).filter_by(user_id=user_id).all()
            
            event_days = set()
            for ev in events:
                if ev.event_time.year == year and ev.event_time.month == month:
                    event_days.add(ev.event_time.day)
            
            return list(event_days)