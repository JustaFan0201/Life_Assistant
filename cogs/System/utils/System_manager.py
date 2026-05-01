from database.db import SessionLocal
from database.models import User, BotSettings

class SystemManager:
    @staticmethod
    def register_user(discord_id: int, username: str):
        """註冊新使用者或更新使用者名稱"""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.discord_id == discord_id).first()
                
                if not user:
                    new_user = User(
                        discord_id=discord_id,
                        username=username,
                    )
                    db.add(new_user)
                    db.commit()
                    print(f"🆕 [Database] 新使用者註冊: {username} ({discord_id})")
                else:
                    if user.username != username:
                        user.username = username
                        db.commit()
                        # print(f"🔄 [Database] 更新使用者名稱: {username}")
                        
        except Exception as e:
            print(f"❌ [Database] 使用者註冊失敗: {e}")

    @staticmethod
    def get_all_dashboard_settings() -> list[dict]:
        """獲取所有已設定 Dashboard 的伺服器頻道資訊"""
        try:
            with SessionLocal() as db:
                all_settings = db.query(BotSettings).filter(BotSettings.dashboard_channel_id.isnot(None)).all()
                
                # 將資料轉換成 dict 列表回傳，避免離開 with 區塊後引發 detached 錯誤
                return [{"guild_id": s.id, "channel_id": s.dashboard_channel_id} for s in all_settings]
                
        except Exception as e:
            print(f"❌ [Dashboard] 讀取資料庫失敗: {e}")
            return []
        
    @staticmethod
    def update_guild_setting(guild_id: int, column_name: str, value: int) -> tuple[bool, str]:
        """更新伺服器的 BotSettings，成功回傳 (True, "")，失敗回傳 (False, 錯誤訊息)"""
        try:
            with SessionLocal() as db:
                settings = db.query(BotSettings).filter(BotSettings.id == guild_id).first()

                # 如果該伺服器還沒有設定檔，就自動建立一個
                if not settings:
                    settings = BotSettings(id=guild_id)
                    db.add(settings)
                
                # 使用 setattr 動態設定欄位名稱
                setattr(settings, column_name, value)
                db.commit()
                return True, ""
                
        except Exception as e:
            return False, str(e)
        
    @staticmethod
    def get_guild_setting(guild_id: int, column_name: str) -> int | None:
        """
        獲取伺服器的特定設定值 (例如取得設定的頻道 ID)
        成功回傳該欄位的值 (整數)，找不到或發生錯誤則回傳 None
        """
        try:
            with SessionLocal() as db:
                settings = db.query(BotSettings).filter(BotSettings.id == guild_id).first()
                
                if not settings:
                    return None
                
                # 使用 getattr 動態取得指定欄位的值
                return getattr(settings, column_name, None)
                
        except Exception as e:
            print(f"❌ [Database] 讀取伺服器設定 ({column_name}) 失敗: {e}")
            return None