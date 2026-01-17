import os
import json
from datetime import datetime, timezone, timedelta
import discord

class ItineraryTools:
    def __init__(self, folder_path):
        self.file_path = os.path.join(folder_path, "itinerary.json")
        self.template = {"data": []}
    
    def read_db(self):
        if not os.path.exists(self.file_path):
            return self.template.copy()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                if os.path.getsize(self.file_path) == 0:
                    return self.template.copy()
                return json.load(f)
        except Exception:
            return self.template.copy()

    def add_and_save(self, new_data, channel_id):
        db = self.read_db()
        check_success, info = self.time_check(new_data)

        if check_success:
            new_data['channel_id'] = channel_id
            db["data"].append(new_data)
            count = len(db["data"])

            try:
                self.order(db)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=4)
              
                return count, True, "success"
            except Exception as e:
                print(f"建立/寫入檔案失敗: {e}")
                return 0, False, "錯誤:建立/寫入檔案失敗 請通知管理員"
            
        else:
            count = len(db["data"])
            return count, False, info


            
    def time_check(self, new_data):
        tz_utc_8 = timezone(timedelta(hours=8))
        now = datetime.now(tz_utc_8)

        try:
            temp = str(new_data['time']).split(':')
            if len(temp) != 2:
                return False, '時間(時:分)填入錯誤 請重式(可能是沒加":")'
            h = new_data["hour"] = int(temp[0])
            mi = new_data["minute"] = int(temp[1])
            del new_data['time']

        except ValueError as e:
            return False, '時間(時:分)填入錯誤 請重式(可能是沒加":")'
        except KeyError as e:
            return False , '錯誤:刪除time屬性失敗 請通知管理員'

        try:
            y = int(new_data["year"])
            m = int(new_data["month"])
            d = int(new_data["date"])

            checked_time = datetime(y, m, d, h, mi, tzinfo=tz_utc_8)

            now_year = datetime.now(tz_utc_8).year
            if not (now_year <= y <= now_year + 2):
                return False, "年份僅限今年至後年"
            
            if checked_time < now:
                return False, "設定的時間已過"
            
            return True, "check success"

        except ValueError as e:
            return False, "時間設定錯誤 請檢查後重試"
        
    def get_data_list(self):
        db = self.read_db()
        data_list = db.get("data", [])
        
        return data_list
    
    def order(self, db):
        db["data"].sort(key=lambda x: (
            int(x.get('priority', 2)), 
            int(x['year']),
            int(x['month']),
            int(x['date']),
            int(x['hour']),
            int(x['minute'])
            
        ))
        return db

    def view_delete_list(self):
        db = self.read_db()
        raw_data = db.get("data", [])
        data_list = []
        priority_map = ["🔴", "🟡", "🟢"]
        
        for index, item in enumerate(raw_data, start=1):
            try:
                priority_emoji = priority_map[int(item['priority'])]
                
                time_str = f"{item['year']}-{int(item['month']):02d}-{int(item['date']):02d} {int(item['hour']):02d}:{int(item['minute']):02d}"
                
                content_preview = item.get('content', '')[:10]
                data_list.append(f"{priority_emoji} #{index} | {time_str} | {content_preview}")
            except Exception as e:

                print(f"第 {index} 筆行程出錯: {e}")
                continue
        
        return data_list
    
    def delete(self, target_index):
        db = self.read_db()
        data_list = db.get("data", [])
        target_index -= 1

        if not (0 <= target_index < len(data_list)):
            return len(data_list), False, "找不到要刪除的行程"

        data_list.pop(target_index)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
            return len(data_list), True, "success"
        except Exception as e:
            return 0, False, f"寫入失敗: {e}"
        
    def mantion_check(self, now_minute):
        db = self.read_db()
        data_list = db.get("data", [])
        # print(now_minute, type(now_minute))
        
        tz_utc_8 = timezone(timedelta(hours=8))
        now = datetime.now(tz_utc_8)
        new_time = now.replace(minute=int(now_minute))
        print(now)

        try:
            new_time = now.replace(minute=now_minute, second=0, microsecond=0)
        except ValueError as e:
            return False, "now_minute不合理 請通知管理員", None
        
        for data in data_list:
            if int(data['minute']) == now_minute:
                try:
                    trans_data = datetime(
                        year=int(data['year']),
                        month=int(data['month']),
                        day=int(data['date']),
                        hour=int(data['hour']),
                        minute=int(data['minute']),
                        tzinfo=tz_utc_8
                    )
                except ValueError as e:
                    return False, "data轉換失敗 請通知管理員", None
                
                try:
                    if new_time == trans_data:
                        return self.trans_mantion_output(data)
                except (ValueError, TypeError) as e:
                    return False, "data比較失敗 請通知管理員", None
        return False, "沒有任務", None
    
    def trans_mantion_output(self, data):
        priority_map = ["🔴緊急", "🟡重要", "🟢普通"]

        try:
            priority_emoji = priority_map[int(data['priority'])]
        except ValueError as e:
                    return False, "priority數值異常 請通知管理員", None

        try:
            infor = f"{data['content']}--在 {data['year']}年--{data['month']}月--{data['date']}日 的 {data['hour']}點{data['minute']}分"
            output = f"{priority_emoji}提醒!\n{infor}"

            return True, output, data['channel_id']
        except (ValueError, TypeError) as e:
            return False, "提醒輸出轉換失敗 請通知管理員", None
        
    def data_self_check(self):
        data_list = self.get_data_list()

        tz_utc_8 = timezone(timedelta(hours=8))
        now = datetime.now(tz_utc_8)
        new_time = now.replace(second=0, microsecond=0)

        db = {"data": []}

        for data in data_list:
            try:
                trans_data = datetime(
                    year=int(data['year']),
                    month=int(data['month']),
                    day=int(data['date']),
                    hour=int(data['hour']),
                    minute=int(data['minute']),
                    tzinfo=tz_utc_8
                )
            except ValueError as e:
                raise Exception("data自檢時轉換失敗")
            
            try:
                if trans_data <= new_time :
                    pass
                else:
                    db['data'].append(data)

            except (ValueError, TypeError) as e:
                raise Exception("data自檢時比較失敗")
            
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise Exception("錯誤:建立/寫入檔案失敗 請通知管理員")
        
            
        