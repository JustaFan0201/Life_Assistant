# database/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import DATABASE_URL

_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 30
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

def init_db() -> bool:
    """初始化資料庫，建立所有 Table
        return True if succeed
    """
    
    print(f"🔹 Engine URL: {_engine.url}")
    try:
        conn = _engine.connect()
        print("✅ 資料庫連線成功")
        conn.close()

        print("正在檢查並建立資料表結構...")
        Base.metadata.create_all(bind=_engine) 
        print("✅ 所有資料表已建立/更新完成 (If not existed)")
        return True

    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False
    # print("✅ 資料庫資料表已建立/更新")
    return True

# Context Manager 用法，確保 Session 會被關閉
class DatabaseSession:
    def __enter__(self):
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()