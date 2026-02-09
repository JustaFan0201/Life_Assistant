# database/__init__.py
from .db import engine, SessionLocal, init_db, DatabaseSession
from .models import Base, User, EmailConfig, EmailContact, THSRProfile, Ticket, BotSettings
from .gmail_manager import EmailDatabaseManager

# 統一匯出清單
__all__ = [
    "engine",
    "SessionLocal",
    "init_db",
    "DatabaseSession",
    "Base",
    "User",
    "EmailConfig",
    "EmailContact",
    "THSRProfile",
    "Ticket",
    "BotSettings",
    "EmailDatabaseManager"
]