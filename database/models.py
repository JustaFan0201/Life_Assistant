# database/models.py
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey, Boolean, Text, JSON, func, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import VECTOR  # pgvector
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

    stocks = relationship("UserStockWatch", back_populates="user", cascade="all, delete-orphan")

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

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    message_text = Column(Text, nullable=False)
    vector = Column(VECTOR(768), nullable=False)  # 768維向量，如果用 e5-large 就改成 1024
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    metadata = Column(JSON, default={})

class TrackerCategory(Base):
    __tablename__ = 'tracker_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)
    
    name = Column(String, nullable=False)
    range_options = Column(JSON, default=lambda: [7, 30, 180, 365])
    current_range = Column(Integer, default=7)
    fields = Column(JSON, nullable=False) 
    
    last_ai_analysis = Column(Text, nullable=True)
    analysis_updated_at = Column(DateTime, nullable=True)

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

class UserStockWatch(Base):
    __tablename__ = 'user_stock_watch'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.discord_id'), nullable=False)

    stock_symbol = Column(String(10), nullable=False) # 股票代碼
    stock_name = Column(String(50), nullable=True)   # 股票名稱
    
    # --- 投資數據核心（精確損益用） ---
    # shares 用來算現值，total_cost 用來算損益基準
    shares = Column(Integer, default=0)               # 持有股數 (取代 quantity)
    total_cost = Column(Float, default=0)             # 總付出成本 (含手續費)
    buy_price = Column(Float, nullable=True)          # 參考買入單價 (選填)
    
    # --- 預警設定 ---
    target_up = Column(Float, nullable=True)          # 漲幅預警 (例如 0.05 代表 5%)
    target_down = Column(Float, nullable=True)        # 跌幅預警 (例如 -0.05 代表 -5%)
    
    # --- 狀態紀錄 ---
    last_notified_price = Column(Float, nullable=True) # 上次通知時的價格
    last_close_price = Column(Float, nullable=True)    # 昨收價 (計算今日漲跌幅用)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="stocks")
