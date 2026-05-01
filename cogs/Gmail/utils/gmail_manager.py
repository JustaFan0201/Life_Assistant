import re
from typing import Optional, Dict
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from database.models import User, EmailConfig, EmailCategory, CategorizedEmail
from config import ENCRYPTION_KEY
class EmailDatabaseManager:
    def __init__(self, session_factory):
        self.Session = session_factory

        self.key = ENCRYPTION_KEY
        if not self.key:
            print("警告: 找不到 ENCRYPTION_KEY，加密功能將無法運作！")
            self.cipher = None
        else:
            self.cipher = Fernet(self.key.encode()) 

    def _encrypt(self, text: str) -> str:
        if not self.cipher or not text: return text
        return self.cipher.encrypt(text.encode()).decode()

    def _decrypt(self, token: str) -> str:
        if not self.cipher or not token: return token
        try:
            return self.cipher.decrypt(token.encode()).decode()
        except Exception:
            return token

    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _ensure_user_exists(self, session: Session, user_id: int):
        user = session.query(User).filter_by(discord_id=user_id).first()
        if not user:
            user = User(discord_id=user_id, username=f"User_{user_id}")
            session.add(user)
            session.flush() 
        return user

    def get_user_config(self, user_id: int) -> Optional[Dict]:
        with self.Session() as session:
            config = session.query(EmailConfig).filter_by(user_id=user_id).first()
            return {
                "email": config.email_address,
                "password": self._decrypt(config.email_password),
                "last_email_id": config.last_email_id
            } if config else None

    def save_user_config(self, user_id: int, email: str, password: str) -> str:
        if not self._is_valid_email(email):
            return "❌ Email 格式不符"
        
        encrypted_password = self._encrypt(password)

        with self.Session() as session:
            try:
                self._ensure_user_exists(session, user_id)
                
                config = session.query(EmailConfig).filter_by(user_id=user_id).first()
                if config:
                    config.email_address = email
                    config.email_password = encrypted_password
                else:
                    new_config = EmailConfig(user_id=user_id, email_address=email, email_password=encrypted_password)
                    session.add(new_config)
                
                session.commit()
                return f"✅ 個人信箱設置成功！\n帳號：`{email}`"
            except Exception as e:
                session.rollback()
                print(f"[Database Error] save_user_config: {e}")
                return f"❌ 設置失敗：資料庫結構可能已變更，請通知管理員。"

    def update_last_email_id(self, user_id: int, last_id: str):
        with self.Session() as session:
            session.query(EmailConfig).filter_by(user_id=user_id).update({"last_email_id": last_id})
            session.commit()

    def get_user_categories(self, user_id: int) -> list[dict]:
        """獲取使用者的所有分類清單"""
        try:
            with self.Session() as session:
                categories = session.query(EmailCategory).filter_by(user_id=user_id).all()
                # 轉成 dict 列表，方便餵給 AI 分析器
                return [{"id": c.id, "name": c.name, "desc": c.description} for c in categories]
        except Exception as e:
            print(f"❌ 取得分類失敗: {e}")
            return []

    def save_categorized_email(self, category_id: int, email_info: dict, summary: str):
        """將 AI 處理完的信件存入對應分類"""
        try:
            with self.Session() as session:
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
        
    def add_category(self, user_id: int, name: str, description: str) -> tuple[bool, str]:
        """新增一個使用者自訂分類"""
        from database.models import EmailCategory
        try:
            with self.Session() as session:
                # 檢查是否重複
                if session.query(EmailCategory).filter_by(user_id=user_id, name=name).first():
                    return False, "⚠️ 已經有相同名稱的分類囉！"
                
                new_cat = EmailCategory(user_id=user_id, name=name, description=description)
                session.add(new_cat)
                session.commit()
                return True, f"✅ 成功建立分類：{name}"
        except Exception as e:
            return False, f"❌ 資料庫錯誤: {e}"

    def delete_category(self, category_id: int) -> bool:
        """刪除指定分類 (關聯的信件也會因為 cascade 自動刪除)"""
        from database.models import EmailCategory
        try:
            with self.Session() as session:
                cat = session.query(EmailCategory).filter_by(id=category_id).first()
                if cat:
                    session.delete(cat)
                    session.commit()
                    return True
                return False
        except Exception:
            return False

    def get_category_emails(self, category_id: int) -> list[dict]:
        """取得該分類下所有的信件 (由新到舊排序)"""
        from database.models import CategorizedEmail
        try:
            with self.Session() as session:
                emails = session.query(CategorizedEmail).filter_by(category_id=category_id)\
                                .order_by(CategorizedEmail.id.desc()).all()
                return [
                    {
                        "subject": e.subject, 
                        "summary": e.ai_summary, 
                        "link": e.gmail_link, 
                        "date": e.received_at
                    } for e in emails
                ]
        except Exception:
            return []