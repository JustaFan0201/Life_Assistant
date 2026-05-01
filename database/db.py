# database/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

        return True

    except Exception as e:
        print(f"❌ 資料庫連線失敗: {e}")
        return False
    # print("✅ 資料庫資料表已建立/更新")
    return True