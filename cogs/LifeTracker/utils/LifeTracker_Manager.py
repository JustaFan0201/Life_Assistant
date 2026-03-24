from database.db import DatabaseSession
from database.models import User, TrackerCategory, TrackerSubCategory
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))

class LifeTrackerDatabaseManager:
    
    @staticmethod
    def create_category(user_id: int, username: str, cat_name: str, fields_list: list[str], subcats_list: list[str]):
        """
        處理建立「主分類」與「子分類」的邏輯，並確保使用者存在。
        """
        with DatabaseSession() as db:
            # 確保使用者存在
            user = db.query(User).filter(User.discord_id == user_id).first()
            if not user:
                user = User(discord_id=user_id, username=username)
                db.add(user)
                db.flush()

            # 建立主分類
            new_category = TrackerCategory(
                user_id=user_id,
                name=cat_name,
                fields=fields_list
            )
            db.add(new_category)
            db.flush() # 取得 new_category.id

            # 建立對應的子分類
            for sub_name in subcats_list:
                new_sub = TrackerSubCategory(
                    category_id=new_category.id,
                    name=sub_name
                )
                db.add(new_sub)

            db.commit()
            return True

    @staticmethod
    def delete_category(category_id: int):
        """刪除整個主分類及其所有子分類與紀錄"""
        with DatabaseSession() as db:
            from database.models import TrackerCategory
            cat = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if cat:
                db.delete(cat)
                db.commit()
                return True
            return False

    @staticmethod
    def get_user_categories(user_id: int):
        """
        取得特定使用者的所有主分類 (未來給下拉選單使用)
        """
        with DatabaseSession() as db:
            categories = db.query(TrackerCategory).filter(TrackerCategory.user_id == user_id).all()
            return categories

    @staticmethod
    def get_category_details(category_id: int):
        """取得單一分類的詳細資訊與它的子分類"""
        with DatabaseSession() as db:
            category = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if not category:
                return None
            
            # 將資料轉為 Dictionary 避免 Session 關閉後無法讀取
            cat_data = {
                "id": category.id,
                "name": category.name,
                "fields": category.fields
            }
            subcats_data = [{"id": s.id, "name": s.name} for s in category.subcategories]
            
            return cat_data, subcats_data

    @staticmethod
    def get_recent_records(category_id: int, page: int = 0, limit: int = 10):
        """取得該分類近期的紀錄 (支援分頁)"""
        with DatabaseSession() as db:
            from database.models import LifeRecord
            
            # 計算 offset (跳過幾筆資料)
            offset = page * limit
            
            # 撈取紀錄，依照時間遞減排序 (最新的在最上面)
            records = db.query(LifeRecord).filter(LifeRecord.category_id == category_id)\
                        .order_by(LifeRecord.created_at.desc())\
                        .offset(offset).limit(limit).all()
            
            # 將紀錄轉為乾淨的 List[dict]
            record_list = []
            for r in records:
                # 💡 [修改] 這裡再也不用去比對 subcategory_id 了，直接讀取快照名稱！
                display_name = r.subcat_name if r.subcat_name else "無標籤"
                
                record_list.append({
                    "id": r.id,
                    "sub_name": display_name,
                    "values": r.values,
                    "note": r.note,
                    "created_at": r.created_at.strftime("%Y/%m/%d")
                })
                
            return record_list

    @staticmethod
    def add_subcategory(category_id: int, subcat_name: str):
        """為指定的分類新增一個子分類"""
        with DatabaseSession() as db:
            new_sub = TrackerSubCategory(category_id=category_id, name=subcat_name)
            db.add(new_sub)
            db.commit()
            return True
        
    @staticmethod
    def add_life_record(user_id: int, category_id: int, subcat_id: int, values_dict: dict, note: str, record_time_str: str = None):
        """新增一筆生活紀錄"""
        with DatabaseSession() as db:
            from database.models import LifeRecord, TrackerSubCategory
            
            # 取得目前的精確時間 (包含時分秒)
            now = datetime.now(TW_TZ)
            
            if record_time_str:
                try:
                    # 解析使用者輸入的日期 (YYYY/MM/DD)
                    parsed_date = datetime.strptime(record_time_str, "%Y/%m/%d")
                    # 結合：使用者的日期 + 系統當下的時分秒
                    final_time = parsed_date.replace(
                        hour=now.hour, 
                        minute=now.minute, 
                        second=now.second, 
                        tzinfo=TW_TZ
                    )
                except ValueError:
                    final_time = now # 解析失敗則用當下時間
            else:
                final_time = now

            snapshot_name = None
            if subcat_id:
                subcat = db.query(TrackerSubCategory).filter(TrackerSubCategory.id == subcat_id).first()
                snapshot_name = subcat.name if subcat else None

            new_record = LifeRecord(
                user_id=user_id,
                category_id=category_id,
                subcategory_id=subcat_id,
                subcat_name=snapshot_name,
                values=values_dict, 
                note=note,
                created_at=final_time
            )
            db.add(new_record)
            db.commit()
            return True
        
    @staticmethod
    def delete_subcategory(subcat_id: int):
        """刪除指定的子分類 (標籤)"""
        with DatabaseSession() as db:
            from database.models import TrackerSubCategory
            subcat = db.query(TrackerSubCategory).filter(TrackerSubCategory.id == subcat_id).first()
            if subcat:
                db.delete(subcat)
                db.commit()
                return True
            return False
        
    @staticmethod
    def get_subcat_stats(category_id: int, target_field: str = None) -> dict:
        """
        取得該分類下各子分類的「數值總和」。
        如果傳入 target_field，就只加總該欄位的數值。
        """
        with DatabaseSession() as db:
            from database.models import LifeRecord
            records = db.query(LifeRecord).filter(LifeRecord.category_id == category_id).all()

            result_dict = {}
            for r in records:
                display_name = r.subcat_name if r.subcat_name else "無標籤"
                amount = 0
                
                if isinstance(r.values, dict):
                    # 如果有指定目標欄位，且該紀錄有這個欄位
                    if target_field and target_field in r.values:
                        try:
                            amount = float(r.values[target_field])
                        except (ValueError, TypeError):
                            pass 
                    # 舊邏輯防呆：如果沒有指定，就抓第一個數字
                    elif not target_field:
                        for val in r.values.values():
                            try:
                                amount = float(val)
                                break 
                            except (ValueError, TypeError):
                                continue 
                
                if display_name not in result_dict:
                    result_dict[display_name] = 0
                result_dict[display_name] += amount

            final_stats = {}
            for k, v in result_dict.items():
                if v > 0:
                    final_stats[k] = int(v) if v.is_integer() else round(v, 2)
                    
            return final_stats
        