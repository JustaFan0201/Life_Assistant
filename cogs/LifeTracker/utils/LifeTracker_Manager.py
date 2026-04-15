from database.db import DatabaseSession
from database.models import User, TrackerCategory, TrackerSubCategory, LifeRecord
from datetime import datetime, timedelta
from config import TW_TZ
import math
from cogs.LifeTracker.LifeTracker_config import (
    MAX_FIELDS,
    MAX_SUBCATS,
    MAX_FIELDS_LENGTH,
    MAX_SUBCAT_LENGTH,
    MAX_MAINCAT_LENGTH,
    MAX_DAY_RANGE,
    MIN_DAY_RANGE,
    MAX_TEXT_LENGTH,
    MAX_INPUT_VALUE
)
class LifeTracker_Manager:
    
    @staticmethod
    def create_category(user_id: int, username: str, cat_name: str, fields_list: list[str], subcats_list: list[str]):
        """
        建立分類的中心邏輯，包含所有合法性檢查
        回傳: (bool, str_or_none) -> (是否成功, 錯誤訊息)
        """
        cat_name = cat_name.strip()
        if not cat_name:
            return False, "分類名稱不能為空。"
        
        if len(cat_name) > MAX_MAINCAT_LENGTH:
            return False, f"分類名稱「{cat_name}」過長，請限制在 {MAX_MAINCAT_LENGTH} 字內。"

        if not fields_list:
            return False, "請至少輸入一個需要紀錄的數值項目（例如：金額）。"
        
        if len(fields_list) > MAX_FIELDS:
            return False, f"數值欄位過多，最多只能設定 {MAX_FIELDS} 個。"
            
        if len(subcats_list) > MAX_SUBCATS:
            return False, f"標籤數量過多，最多只能設定 {MAX_SUBCATS} 個。"

        if len(fields_list) != len(set(fields_list)):
            return False, "數值欄位名稱不能重複。"

        if len(subcats_list) != len(set(subcats_list)):
            return False, "標籤名稱不能重複。"

        for field in fields_list:
            if len(field) > MAX_FIELDS_LENGTH:
                return False, f"數值欄位「{field}」過長，請限制在 {MAX_FIELDS_LENGTH} 字內。"

        for sub in subcats_list:
            if len(sub) > MAX_SUBCAT_LENGTH:
                return False, f"標籤「{sub}」過長，請限制在 {MAX_SUBCAT_LENGTH} 字內。"

        with DatabaseSession() as db:
            existing = db.query(TrackerCategory).filter(
                TrackerCategory.user_id == user_id,
                TrackerCategory.name == cat_name
            ).first()
            if existing:
                return False, f"主分類「{cat_name}」已經存在了。"

            user = db.query(User).filter(User.discord_id == user_id).first()
            if not user:
                user = User(discord_id=user_id, username=username)
                db.add(user)
                db.flush()

            new_category = TrackerCategory(
                user_id=user_id,
                name=cat_name,
                fields=fields_list,
                range_options=[7, 30, 180, 365],
            )
            db.add(new_category)
            db.flush()

            for sub_name in subcats_list:
                new_sub = TrackerSubCategory(
                    category_id=new_category.id,
                    name=sub_name
                )
                db.add(new_sub)

            db.commit()
            return True, None
    
    @staticmethod
    def delete_category(category_id: int):
        """刪除整個主分類及其所有子分類與紀錄"""
        with DatabaseSession() as db:
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
        """取得單一分類詳情，包含區間選項與目前預設區間"""
        with DatabaseSession() as db:
            category = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if not category:
                return None

            cat_data = {
                "id": category.id,
                "name": category.name,
                "fields": category.fields,
                "range_options": category.range_options,
                "current_range": category.current_range,
                "last_ai_analysis": category.last_ai_analysis,
                "analysis_updated_at": category.analysis_updated_at
            }
            subcats_data = [{"id": s.id, "name": s.name} for s in category.subcategories]
            
            return cat_data, subcats_data

    @staticmethod
    def get_recent_records(category_id: int, page: int = 0, limit: int = 10, range_days: int = None):
        """取得紀錄與總頁數 (支援時間區間過濾)"""
        with DatabaseSession() as db:
            from database.models import LifeRecord
            from datetime import datetime, timedelta
            from config import TW_TZ
            
            query = db.query(LifeRecord).filter(LifeRecord.category_id == category_id)
            
            if range_days:
                start_date = datetime.now(TW_TZ) - timedelta(days=int(range_days))
                query = query.filter(LifeRecord.created_at >= start_date)
            
            total_count = query.count()
            
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
            
            offset = page * limit
            records = query.order_by(LifeRecord.created_at.desc())\
                           .offset(offset).limit(limit).all()
            
            record_list = []
            for r in records:
                record_list.append({
                    "id": r.id,
                    "sub_name": r.subcat_name or "其他",
                    "values": r.values,
                    "note": r.note,
                    "created_at": r.created_at.strftime("%Y/%m/%d")
                })
            
            return record_list, total_pages
        
    @staticmethod
    def validate_record_data(category_id: int, values_dict: dict, note: str, record_time_str: str):
        """
        專門校驗紀錄數據的合法性 (不涉及寫入)
        回傳: (bool, str_or_none)
        """
        try:
            datetime.strptime(record_time_str, "%Y/%m/%d")
        except (ValueError, TypeError):
            return False, "日期格式錯誤 (應為 YYYY/MM/DD)。"

        if note and len(note) > MAX_TEXT_LENGTH:
            return False, f"備註太長了，請限制在 {MAX_TEXT_LENGTH} 字內。"

        with DatabaseSession() as db:
            cat = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if not cat:
                return False, "找不到對應的分類。"

            for f_name in cat.fields:
                val = values_dict.get(f_name)
                if val is None or str(val).strip() == "":
                    return False, f"欄位「{f_name}」尚未填寫。"
                
                try:
                    num = float(str(val).strip())
                    if num < 0:
                        return False, f"欄位「{f_name}」不能為負數。"
                    if num > MAX_INPUT_VALUE:
                        return False, f"欄位「{f_name}」數值過大，最高限制 {MAX_INPUT_VALUE:,}。"
                except ValueError:
                    return False, f"欄位「{f_name}」必須是有效的數字。"

        return True, None

    @staticmethod
    def add_life_record(user_id: int, category_id: int, subcat_id: int, values_dict: dict, note: str, record_time_str: str = None):
        """新增一筆生活紀錄 (包含最終校驗)"""
        is_valid, error = LifeTracker_Manager.validate_record_data(category_id, values_dict, note, record_time_str)
        if not is_valid:
            return False, error

        with DatabaseSession() as db:
            now = datetime.now(TW_TZ)
            parsed_date = datetime.strptime(record_time_str, "%Y/%m/%d")
            final_time = parsed_date.replace(hour=now.hour, minute=now.minute, second=now.second, tzinfo=TW_TZ)

            snapshot_name = "其他"
            if subcat_id:
                subcat = db.query(TrackerSubCategory).filter(TrackerSubCategory.id == subcat_id).first()
                if subcat: snapshot_name = subcat.name

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
            return True, None

    @staticmethod
    def add_subcategory(category_id: int, subcat_names_list: list[str]):
        """
        新增標籤的中心邏輯
        回傳: (bool, str_or_none)
        """
        if not subcat_names_list:
            return False, "請至少輸入一個標籤名稱。"

        if len(subcat_names_list) != len(set(subcat_names_list)):
            return False, "輸入的標籤名稱中有重複項。"

        for name in subcat_names_list:
            if len(name) > MAX_SUBCAT_LENGTH:
                return False, f"標籤「{name}」過長，請限制在 {MAX_SUBCAT_LENGTH} 字內。"

        with DatabaseSession() as db:
            existing_subcats = db.query(TrackerSubCategory).filter(
                TrackerSubCategory.category_id == category_id
            ).all()
            existing_names = [s.name for s in existing_subcats]

            for name in subcat_names_list:
                if name in existing_names:
                    return False, f"標籤「{name}」已經存在於此分類中。"

            if len(existing_names) + len(subcat_names_list) > MAX_SUBCATS:
                return False, f"標籤數量超過上限 {MAX_SUBCATS} 個。"

            for name in subcat_names_list:
                new_sub = TrackerSubCategory(category_id=category_id, name=name)
                db.add(new_sub)
            
            db.commit()
            return True, None

    @staticmethod
    def update_subcategory_name(category_id: int, subcat_id: int, new_name: str):
        """
        修改標籤名稱的中心邏輯
        回傳: (bool, str_or_none)
        """
        new_name = new_name.strip()
        if not new_name:
            return False, "名稱不能為空。"

        if len(new_name) > MAX_SUBCAT_LENGTH:
            return False, f"標籤名稱過長，請限制在 {MAX_SUBCAT_LENGTH} 字內。"

        with DatabaseSession() as db:
            conflict = db.query(TrackerSubCategory).filter(
                TrackerSubCategory.category_id == category_id,
                TrackerSubCategory.name == new_name,
                TrackerSubCategory.id != subcat_id
            ).first()
            
            if conflict:
                return False, f"標籤「{new_name}」已存在，請換一個名字。"

            subcat = db.query(TrackerSubCategory).filter(TrackerSubCategory.id == subcat_id).first()
            if subcat:
                db.query(LifeRecord).filter(LifeRecord.subcategory_id == subcat_id).update({
                    "subcat_name": new_name
                })
                subcat.name = new_name
                db.commit()
                return True, None
            
            return False, "找不到該標籤。"

    @staticmethod
    def delete_subcategory(subcat_id: int):
        """
        刪除指定的子分類 (標籤)
        核心邏輯：在刪除標籤前，將所有關聯紀錄的 ID 設為 None，並將快照名稱更新為「其他」
        """
        with DatabaseSession() as db: 
            subcat = db.query(TrackerSubCategory).filter(TrackerSubCategory.id == subcat_id).first()
            
            if subcat:
                try:
                    db.query(LifeRecord).filter(LifeRecord.subcategory_id == subcat_id).update({
                        "subcategory_id": None,
                        "subcat_name": "其他"
                    }, synchronize_session=False)
                    
                    db.delete(subcat)
                    db.commit()
                    return True
                except Exception as e:
                    db.rollback()
                    print(f"[Error] 刪除標籤失敗: {e}")
                    return False
            return False
        
    @staticmethod
    def get_subcat_stats(category_id: int, target_field: str, range_days: int = 7) -> dict:
        """
        取得該分類下各子分類的「數值總和」。
        如果傳入 target_field，就只加總該欄位的數值。
        """
        with DatabaseSession() as db:
            now = datetime.now(TW_TZ)
            start_date = now - timedelta(days=int(range_days)) 

            records = db.query(LifeRecord).filter(
                LifeRecord.category_id == category_id,
                LifeRecord.created_at >= start_date
            ).all()

            result_dict = {}
            for r in records:
                display_name = r.subcat_name if r.subcat_name else "其他"
                amount = 0
                
                if isinstance(r.values, dict):
                    if target_field and target_field in r.values:
                        try:
                            amount = float(r.values[target_field])
                        except (ValueError, TypeError):
                            pass 
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

    @staticmethod
    def get_records_for_analysis(category_id: int, range_type: str = "week"):
        """
        根據指定的範圍撈取紀錄：'week' (7天), 'month' (30天), 'half_year' (180天)
        """
        with DatabaseSession() as db:
            
            now = datetime.now(TW_TZ)
            if range_type == "week":
                start_date = now - timedelta(days=7)
            elif range_type == "month":
                start_date = now - timedelta(days=30)
            elif range_type == "half_year":
                start_date = now - timedelta(days=180)
            else:
                start_date = now - timedelta(days=7)

            records = db.query(LifeRecord).filter(
                LifeRecord.category_id == category_id,
                LifeRecord.created_at >= start_date
            ).order_by(LifeRecord.created_at.asc()).all()
            
            if not records:
                return None

            data_str = f"--- 紀錄範圍：自 {start_date.strftime('%Y/%m/%d')} 起 ---\n"
            for r in records:
                val_text = ", ".join([f"{k}:{v}" for k, v in r.values.items()])
                data_str += f"- {r.created_at.strftime('%m/%d')} | {r.subcat_name or '其他'} | {val_text} | {r.note or '無'}\n"
            
            return data_str
        
    @staticmethod
    def delete_range_option(category_id: int, days: int):
        """刪除一個時間區間選項 (保留至少一個)"""
        with DatabaseSession() as db:
            cat = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if cat and cat.range_options:
                options = list(cat.range_options)
                if days in options and len(options) > 1:
                    options.remove(days)
                    cat.range_options = options
                    
                    if hasattr(cat, 'current_range'):
                        if cat.current_range == days:
                            cat.current_range = options[0]
                    
                    db.commit()
                    return True
            return False

    @staticmethod
    def update_current_range(category_id: int, days: int):
        """更新目前正在檢視的區間 (持久化)"""
        with DatabaseSession() as db:
            cat = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if cat:
                cat.current_range = days
                db.commit()

    @staticmethod
    def add_range_option(category_id: int, days_input):
        """
        新增時間區間的中心邏輯
        回傳: (bool, str_or_none)
        """
        try:
            days = int(str(days_input).strip())
        except (ValueError, TypeError):
            return False, "天數必須是有效的整數數字。"
        
        if days < MIN_DAY_RANGE or days > MAX_DAY_RANGE:
            return False, f"天數不在範圍中！請設定在 {MIN_DAY_RANGE} ~ {MAX_DAY_RANGE} 之間。"

        with DatabaseSession() as db:
            cat = db.query(TrackerCategory).filter(TrackerCategory.id == category_id).first()
            if not cat:
                return False, "找不到該分類資料。"

            options = list(cat.range_options) if isinstance(cat.range_options, list) else [7, 30, 180, 365]

            if days not in options:
                options.append(days)
                options.sort()
                cat.range_options = options
            
            cat.current_range = days
            db.commit()
            return True, None
        
    @staticmethod
    def add_voice_record(user_id: int, ai_result: dict):
        """
        處理來自語音/AI 解析的紀錄結果
        """
        category_id = ai_result.get("category_id")
        subcat_name_from_ai = ai_result.get("subcat_name")
        values = ai_result.get("values", {})
        note = ai_result.get("note", "")

        with DatabaseSession() as db:
            
            # 1. 根據 AI 給的分類 ID 與 標籤名稱，找尋資料庫中對應的 subcat_id
            subcat = db.query(TrackerSubCategory).filter(
                TrackerSubCategory.category_id == category_id,
                TrackerSubCategory.name == subcat_name_from_ai
            ).first()

            # 2. 如果找到了就拿 ID，沒找到（例如 AI 歸類為「其他」）就給 None
            subcat_id = subcat.id if subcat else None

        return LifeTracker_Manager.add_life_record(
            user_id=user_id,
            category_id=category_id,
            subcat_id=subcat_id,
            values_dict=values,
            note=note
        )