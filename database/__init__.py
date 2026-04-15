# database/__init__.py
from .db import init_db
from .models import Base, User, EmailConfig, EmailContact, BotSettings, CalendarEvent

# 統一匯出清單
__all__ = [
    "init_db",
    "SessionLocal",
    "Base",
    "User",
    "EmailConfig",
    "EmailContact",
    "BotSettings",
    "CalendarEvent"
]