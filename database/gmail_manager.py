import re
from typing import Optional, Dict
import os 
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from .models import User, EmailConfig, EmailContact

class EmailDatabaseManager:
    def __init__(self, session_factory):
        self.Session = session_factory

        self.key = os.getenv("ENCRYPTION_KEY")
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

    def get_all_contacts(self, user_id: int) -> Dict[str, str]:
        with self.Session() as session:
            contacts = session.query(EmailContact).filter_by(user_id=user_id).all()
            return {c.nickname: c.email_address for c in contacts}

    def add_and_save(self, name: str, email: str, user_id: int) -> str:
        if not self._is_valid_email(email):
            return "❌ Email 格式不符"

        with self.Session() as session:
            try:
                self._ensure_user_exists(session, user_id)
                
                if session.query(EmailContact).filter_by(user_id=user_id, nickname=name).first():
                    return f"⚠️ 暱稱「{name}」已存在。"

                session.add(EmailContact(user_id=user_id, nickname=name, email_address=email))
                session.commit()
                return f"✅ 成功新增聯絡人：{name}"
            except Exception as e:
                session.rollback()
                return f"❌ 寫入失敗: {e}"

    def update_contact(self, user_id: int, nickname: str, new_email: str) -> str:
        if not self._is_valid_email(new_email):
            return "❌ Email 格式不符"

        with self.Session() as session:
            contact = session.query(EmailContact).filter_by(user_id=user_id, nickname=nickname).first()
            if contact:
                contact.email_address = new_email
                session.commit()
                return f"✅ 已更新「{nickname}」的地址。"
            return "❌ 找不到該聯絡人"

    def delete_contact(self, user_id: int, nickname: str) -> str:
        with self.Session() as session:
            contact = session.query(EmailContact).filter_by(user_id=user_id, nickname=nickname).first()
            if contact:
                session.delete(contact)
                session.commit()
                return f"🗑️ 已刪除聯絡人：{nickname}"
            return "❌ 找不到該聯絡人"