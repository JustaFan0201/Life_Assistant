import re
from typing import Optional, Dict
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from database.models import EmailConfig, EmailCategory, CategorizedEmail
from database.db_utils import with_db_decorator, get_user
from config import ENCRYPTION_KEY

class EmailDatabaseManager:
    key = ENCRYPTION_KEY
    if not key:
        print("警告: 找不到 ENCRYPTION_KEY，加密功能將無法運作！")
        cipher = None
    else:
        cipher = Fernet(key.encode())

    def __init__(self, session_factory):
        self.session = session_factory

    @staticmethod
    def _encrypt(text: str) -> str:
        if not EmailDatabaseManager.cipher or not text: return text
        return EmailDatabaseManager.cipher.encrypt(text.encode()).decode()

    @staticmethod
    def _decrypt(token: str) -> str:
        if not EmailDatabaseManager.cipher or not token: return token
        try:
            return EmailDatabaseManager.cipher.decrypt(token.encode()).decode()
        except Exception:
            return token


    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


    @staticmethod
    @with_db_decorator
    def get_user_config(user_id: int, db=None) -> Optional[Dict]:
        config = db.query(EmailConfig).filter_by(user_id=user_id).first()
        return {
            "email": config.email_address,
            "password": EmailDatabaseManager._decrypt(config.email_password),
            "last_email_id": config.last_email_id
        } if config else None


    @staticmethod
    @with_db_decorator
    def save_user_config(user_id: int, user_name: str, email: str, password: str, db=None) -> str:
        if not EmailDatabaseManager._is_valid_email(email):
            return "❌ Email 格式不符"
        
        encrypted_password = EmailDatabaseManager._encrypt(password)

        get_user(user_id, user_name, db)
        
        config = db.query(EmailConfig).filter_by(user_id=user_id).first()
        if config:
            config.email_address = email
            config.email_password = encrypted_password
        else:
            new_config = EmailConfig(user_id=user_id, email_address=email, email_password=encrypted_password)
            db.add(new_config)
        
        db.commit()
        return f"✅ 個人信箱設置成功！\n帳號：`{email}`"
        

    def update_last_email_id(self, user_id: int, last_id: str):
        with self.session() as session:
            session.query(EmailConfig).filter_by(user_id=user_id).update({"last_email_id": last_id})
            session.commit()


    @staticmethod
    @with_db_decorator
    def get_user_categories(user_id: int, db=None) -> list[dict]:
        """獲取使用者的所有分類清單"""
        categories = db.query(EmailCategory).filter_by(user_id=user_id).all()
        # 轉成 dict 列表，方便餵給 AI 分析器
        return [{"id": c.id, "name": c.name, "desc": c.description} for c in categories]


    def save_categorized_email(self, category_id: int, email_info: dict, summary: str):
        """將 AI 處理完的信件存入對應分類"""
        try:
            with self.session() as session:
                new_email = CategorizedEmail(
                    category_id=category_id,
                    subject=email_info.get('subject', '(無主旨)')[:100], # 避免主旨過長
                    ai_summary=summary,
                    gmail_link=email_info.get('link', ''), # 這是我們上一步在 gmail_tool 抓到的連結
                    received_at=email_info.get('date', '未知時間')
                )
                session.add(new_email)
                session.commit()
                return True
        except Exception as e:
            print(f"❌ 儲存分類信件失敗: {e}")
            return False
        

    @staticmethod
    @with_db_decorator
    def add_category(user_id: int, name: str, description: str, db=None) -> tuple[bool, str]:
        """新增一個使用者自訂分類"""
        from database.models import EmailCategory
        
        # 檢查是否重複
        if db.query(EmailCategory).filter_by(user_id=user_id, name=name).first():
            return False, "⚠️ 已經有相同名稱的分類囉！"
        
        new_cat = EmailCategory(user_id=user_id, name=name, description=description)
        db.add(new_cat)
        db.commit()
        return True, f"✅ 成功建立分類：{name}"


    @staticmethod
    @with_db_decorator
    def delete_category(*, category_name: str=None, category_id: int=None, db=None) -> bool:
        """刪除指定分類 (關聯的信件也會因為 cascade 自動刪除)"""
        if (category_id is None) == (category_name is None):
            raise ValueError("delete_category: 必須且只能提供 category_id 或 category_name 其中一個")
        
        from database.models import EmailCategory
        if category_id:
            cat = db.query(EmailCategory).filter_by(id=category_id).first()
        else:
            cat = db.query(EmailCategory).filter_by(name=category_name).first()
        
        if cat:
            db.delete(cat)
            db.commit()
            return True
        return False
        

    @staticmethod
    @with_db_decorator
    def get_category_emails(category_id: int, db=None) -> list[dict]:
        """取得該分類下所有的信件 (由新到舊排序)"""
        from database.models import CategorizedEmail    
        emails = db.query(CategorizedEmail).filter_by(category_id=category_id)\
                        .order_by(CategorizedEmail.id.desc()).all()
        return [
            {
                "subject": e.subject, 
                "summary": e.ai_summary, 
                "link": e.gmail_link, 
                "date": e.received_at
            } for e in emails
        ]
