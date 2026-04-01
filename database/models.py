# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class BotSettings(Base):
    __tablename__ = 'bot_settings'

    id = Column(BigInteger, primary_key=True, autoincrement=False) 
    
    dashboard_channel_id = Column(BigInteger, nullable=True)
    login_notify_channel_id = Column(BigInteger, nullable=True)
    calendar_notify_channel_id = Column(BigInteger, nullable=True)
    gpt_channel_id = Column(BigInteger, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = 'users'

    discord_id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    email_config = relationship("EmailConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    email_contacts = relationship("EmailContact", back_populates="user", cascade="all, delete-orphan")

    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")

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

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    description = Column(Text, nullable=True)
    event_time = Column(DateTime, nullable=False)
    is_private = Column(Boolean, default=True)
    priority = Column(String(10), default="2")
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="calendar_events")

class TrackerCategory(Base):
    __tablename__ = 'tracker_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    
    name = Column(String, nullable=False)
    
    # 這裡存儲該分類需要輸入哪些「數值欄位」 (使用 JSON 陣列)
    # 例如：["花費金額"] 或 ["運動時間(分)", "消耗卡路里"]
    fields = Column(JSON, nullable=False) 
    
    created_at = Column(DateTime, default=datetime.now)

    subcategories = relationship("TrackerSubCategory", back_populates="category", cascade="all, delete-orphan")
    records = relationship("LifeRecord", back_populates="category", cascade="all, delete-orphan")

class TrackerSubCategory(Base):
    __tablename__ = 'tracker_subcategories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('tracker_categories.id'), nullable=False)
    
    name = Column(String, nullable=False)

    category = relationship("TrackerCategory", back_populates="subcategories")
    records = relationship("LifeRecord", back_populates="subcategory")

class LifeRecord(Base):
    __tablename__ = 'life_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('tracker_categories.id'), nullable=False)
    
    # 保留 ID 關聯
    subcategory_id = Column(Integer, ForeignKey('tracker_subcategories.id'), nullable=True)
    
    subcat_name = Column(String, nullable=True) 
    
    values = Column(JSON, nullable=False) 
    note = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.now)

    category = relationship("TrackerCategory", back_populates="records")
    subcategory = relationship("TrackerSubCategory", back_populates="records")