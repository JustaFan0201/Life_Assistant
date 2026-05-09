from datetime import datetime, timedelta
from database import SessionLocal
from database.models import EInvoiceConfig
from cogs.LifeTracker.utils import Crypto_Helper
from config import TW_TZ
import calendar
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
        """獲取使用者的發票平台設定，回傳包含明文密碼與最後擷取日期的字典"""
        with SessionLocal() as db:
            config = db.query(EInvoiceConfig).filter_by(user_id=user_id).first()
            if not config:
                return None
            
            try:
                decrypted_password = Crypto_Helper.decrypt(config.password)
                return {
                    "phone_number": config.phone_number,
                    "password": decrypted_password,
                    "last_fetch_date": config.last_fetch_date
                }
            except Exception as e:
                print(f"❌ 密碼解密失敗 (可能是金鑰被更換過): {e}")
                return None

    @staticmethod
    def calculate_fetch_date_range(last_fetch_date) -> tuple[str, str]:
        """
        根據資料庫的 last_fetch_date 計算要抓取的起訖日期字串 (YYYY-MM-DD)。
        """
        now_tw = datetime.now(TW_TZ)
        
        end_date = now_tw 
        
        if last_fetch_date is None:
            # 狀況 1：從未擷取過，預設往回推 29 天
            start_date = end_date - timedelta(days=29)
        else:
            # 狀況 2：曾經擷取過，從上次擷取的日期開始抓
            start_date = datetime.combine(last_fetch_date, datetime.min.time()).replace(tzinfo=TW_TZ)
            
            # (防護機制) 如果很久沒開機器人，限制最多抓取過去 30 天
            if (end_date - start_date).days > 30:
                start_date = end_date - timedelta(days=30)
                
        # 直接把 start_date 變成 end_date 那個月份的 1 號！
        if start_date.year != end_date.year or start_date.month != end_date.month:
            start_date = end_date.replace(day=1)
                
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    @staticmethod
    def update_last_fetch_date(user_id: int, end_date_str: str) -> bool:
        """爬蟲執行成功後，將資料庫的最後擷取日期更新為這次抓取的結束日期"""
        try:
            with SessionLocal() as db:
                config = db.query(EInvoiceConfig).filter_by(user_id=user_id).first()
                if config:
                    # 將 "YYYY-MM-DD" 字串轉回 Python 的 Date 物件並存入資料庫
                    config.last_fetch_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    db.commit()
                    return True
        except Exception as e:
            print(f"❌ 更新最後擷取日期失敗: {e}")
        return False