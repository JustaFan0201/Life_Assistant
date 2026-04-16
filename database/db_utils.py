"""
db_utils.py

Common database utility functions.
"""

from sqlalchemy import Column
from database.db import SessionLocal
from sqlalchemy.orm import Session
from database.models import BotSettings, User
from functools import wraps
import inspect

def with_db_decorator(func):
    """
    Automatically provides a database session ('db') to the function.
    If no 'db' is passed, a new session is created and closed after execution.
    If an error occurs during connection, it will return None; otherwise it returns original function's result.
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
            print(f"{func.__module__}.{func.__name__}: ❌ 資料庫互動失敗: {e}")
            return None
        finally:
            if need_close:
                db.close()
    return wrapper


# BotSettings getter
@with_db_decorator
def get_botsettings(column: Column, db: Session, ID):
    row = db.query(column).filter(BotSettings.id == ID).first()
    
    if row is None:
        print(f"讀取 {column.key} 失敗 (資料不存在)")
        return None

    item = row[0]  # 因為 query 單一欄位，first() 回傳 tuple
    return item


# BotSettings setter
@with_db_decorator
def set_botsettings(column: Column, db: Session, value, ID):
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


# get the user with
@with_db_decorator
def get_user(db: Session, discord_id): 
    user =  db.query(User).filter_by(discord_id=discord_id).first()
    if not user:
        user = User(discord_id=discord_id, username=f"User_{discord_id}")
        db.add(user)
        db.flush() 
    return user