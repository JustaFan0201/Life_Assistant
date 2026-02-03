# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# 1. 系統設定表 (單行模式: ID 固定為 1)
class BotSettings(Base):
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 這裡定義你要存的所有頻道 ID
    dashboard_channel_id = Column(BigInteger, nullable=True)      # 主控台頻道
    login_notify_channel_id = Column(BigInteger, nullable=True)   # 登入通知頻道
    
    # 未來如果要加其他設定，直接在這裡加欄位即可
    # example_role_id = Column(BigInteger, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = 'users'
    discord_id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String)
    personal_id = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    tgo_id = Column(String, nullable=True)
    tickets = relationship("Ticket", back_populates="user")

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'))
    pnr = Column(String)
    train_date = Column(String)
    train_code = Column(String)
    departure = Column(String)
    arrival = Column(String)
    start_station = Column(String)
    end_station = Column(String)
    price = Column(String)
    seats = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="tickets")