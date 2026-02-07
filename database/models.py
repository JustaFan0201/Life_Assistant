# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

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
    created_at = Column(DateTime, default=datetime.now)

    thsr_profile = relationship("THSRProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="user")

    email_config = relationship("EmailConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    email_contacts = relationship("EmailContact", back_populates="user", cascade="all, delete-orphan")

class THSRProfile(Base):
    __tablename__ = 'thsr_profiles'

    user_id = Column(BigInteger, ForeignKey('users.discord_id'), primary_key=True)
    
    personal_id = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    tgo_id = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user = relationship("User", back_populates="thsr_profile")

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'))
    
    pnr = Column(String)          # 訂位代號
    train_date = Column(String)   # 日期
    train_code = Column(String)   # 車次
    departure = Column(String)    # 出發時間
    arrival = Column(String)      # 抵達時間
    start_station = Column(String)# 起點
    end_station = Column(String)  # 終點
    price = Column(String)        # 價格
    seats = Column(String)        # 座位
    is_paid = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    user = relationship("User", back_populates="tickets")

class EmailConfig(Base):
    __tablename__ = 'email_configs'

    user_id = Column(BigInteger, ForeignKey('users.discord_id'), primary_key=True)
    
    email_address = Column(String, nullable=False)
    email_password = Column(String, nullable=False)
    last_email_id = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", back_populates="email_config")

class EmailContact(Base):
    __tablename__ = 'email_contacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    
    nickname = Column(String, nullable=False)
    email_address = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="email_contacts")