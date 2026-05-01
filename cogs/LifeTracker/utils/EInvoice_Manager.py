from database import SessionLocal
from database.models import EInvoiceConfig
from cogs.LifeTracker.utils import Crypto_Helper

class EInvoice_Manager:
    @staticmethod
    def save_config(user_id: int, phone: str, raw_password: str) -> bool:
        """加密並儲存使用者的發票平台帳號密碼"""
        try:
            encrypted_password = Crypto_Helper.encrypt(raw_password)
            
            with SessionLocal() as db:
                config = db.query(EInvoiceConfig).filter_by(user_id=user_id).first()
                if not config:
                    config = EInvoiceConfig(user_id=user_id)
                    db.add(config)
                
                config.phone_number = phone
                config.password = encrypted_password
                db.commit()
                return True
        except Exception as e:
            print(f"❌ 儲存發票設定失敗: {e}")
            return False

    @staticmethod
    def get_config(user_id: int) -> dict:
        """獲取使用者的發票平台設定，回傳包含明文密碼的字典"""
        with SessionLocal() as db:
            config = db.query(EInvoiceConfig).filter_by(user_id=user_id).first()
            if not config:
                return None
            
            try:
                decrypted_password = Crypto_Helper.decrypt(config.password)
                return {
                    "phone_number": config.phone_number,
                    "password": decrypted_password
                }
            except Exception as e:
                print(f"❌ 密碼解密失敗 (可能是金鑰被更換過): {e}")
                return None