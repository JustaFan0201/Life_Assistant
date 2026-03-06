# database/__init__.py
from .db import init_db, DatabaseSession
from .models import Base, User, EmailConfig, EmailContact, THSRProfile, Ticket, BotSettings, CalendarEvent
from .gmail_manager import EmailDatabaseManager
from .calendar_manager import CalendarDatabaseManager

# 統一匯出清單
__all__ = [
    "init_db",
    "DatabaseSession",
    "Base",
    "User",
    "EmailConfig",
    "EmailContact",
    "THSRProfile",
    "Ticket",
    "BotSettings",
    "CalendarEvent",
    "EmailDatabaseManager",
    "CalendarDatabaseManager"
]