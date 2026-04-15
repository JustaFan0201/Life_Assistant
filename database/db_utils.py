"""
db_utils.py

Common database utility functions.
"""

from sqlalchemy import Column
from database.db import SessionLocal
from database.models import BotSettings
from functools import wraps
import inspect

def with_db_decorator(func):
    """
    Automatically provides a database session ('db') to the function.
    If no 'db' is passed, a new session is created and closed after execution.
    """
    sig = inspect.signature(func)
    @wraps(func)
    def wrapper(*args, **kwargs):
        # use the existing db if it exists; otherwise, create a new one
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        db = bound.arguments.get("db", None)
        need_close = False
        if db is None:
            db = SessionLocal()
            bound.arguments["db"] = db
            need_close = True
        try:
            return func(*bound.args, **bound.kwargs)
        except Exception as e:
            print(f"❌ 資料庫互動失敗: {e}")
        finally:
            if need_close:
                db.close()
    return wrapper


# BotSettings getter
@with_db_decorator
def get_botsettings(column: Column, ID=1):
    try:
        with SessionLocal() as db:
            row = db.query(column).filter(BotSettings.id == ID).first()
            
            if row is None:
                print(f"讀取 {column.key} 失敗 (資料不存在)")
                return None

            item = row[0]  # 因為 query 單一欄位，first() 回傳 tuple
            return item

    except Exception as e:
        print(f"❌ 讀取資料庫設定失敗: {e}")
        return None


# BotSettings setter
def set_botsettings(column: Column, value, ID=1):
    try:
        with SessionLocal() as db:
            # 取得整個物件
            obj = db.query(BotSettings).filter(BotSettings.id == ID).first()
            
            if not obj:
                print(f"找不到 ID={ID} 的資料 自動新增一個")
                obj = BotSettings(id=ID)
                db.add(obj)

            # 更新欄位
            setattr(obj, column.key, value)
            
            db.commit()
            print(f"✅ 更新 {column.key} 成功，值={value}")
            return True

    except Exception as e:
        print(f"❌ 更新資料庫失敗: {e}")
        return False

# get the user with
def get_user(discord_id): 
    user = session.query(User).filter_by(discord_id=user_id).first()
    if not user:
        user = User(discord_id=user_id, username=f"User_{user_id}")
        session.add(user)
        session.flush() 
    return user