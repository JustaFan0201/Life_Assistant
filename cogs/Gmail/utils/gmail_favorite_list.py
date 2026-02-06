import os
import json
import re

class EmailFavoriteList:
    def __init__(self, folder_path):
        self.file_path = os.path.join(folder_path, "email_list.json")
        self.template = {"data": {}, "configs": {}}

    def read_db(self):
        if not os.path.exists(self.file_path):
            return self.template.copy()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                if os.path.getsize(self.file_path) == 0:
                    return self.template.copy()
                db = json.load(f)
                
                if "data" not in db: db["data"] = {}
                if "configs" not in db: db["configs"] = {}
                return db
        except Exception:
            return self.template.copy()

    def save_user_config(self, user_id, email, password):
        db = self.read_db()
        uid = str(user_id)
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email) is None:
            return "❌ Email 格式不符"

        last_id = db["configs"].get(uid, {}).get("last_email_id")
        
        db["configs"][uid] = {
            "email": email,
            "password": password,
            "last_email_id": last_id
        }
        
        try:
            self._save_to_file(db)
            return f"✅ 個人信箱設置成功！\n帳號：`{email}`"
        except Exception as e:
            return f"❌ 設置失敗: {e}"

    def get_user_config(self, user_id):
        db = self.read_db()
        return db.get("configs", {}).get(str(user_id))

    def add_and_save(self, name, email, user_id):
        db = self.read_db() 
        uid = str(user_id)

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email) is None:
            return "❌ email 格式不符"

        if uid not in db["data"]:
            db["data"][uid] = {}

        if name in db["data"][uid]:
            return f"⚠️ 暱稱「{name}」已存在，請換一個名字。"

        db["data"][uid][name] = email

        try:
            self._save_to_file(db)
            return f"✅ 成功新增聯絡人：{name} ({email})"
        except Exception as e:
            return f"❌ 寫入失敗: {e}"
        
    def update_contact(self, user_id, nickname, new_email):
        db = self.read_db()
        uid = str(user_id)
        if uid in db["data"] and nickname in db["data"][uid]:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, new_email) is None:
                return "❌ Email 格式不符"
            
            db["data"][uid][nickname] = new_email
            self._save_to_file(db)
            return f"✅ 已將「{nickname}」的地址更新為：{new_email}"
        return "❌ 找不到該聯絡人"

    def delete_contact(self, user_id, nickname):
        db = self.read_db()
        uid = str(user_id)
        if uid in db["data"] and nickname in db["data"][uid]:
            del db["data"][uid][nickname]
            self._save_to_file(db)
            return f"🗑️ 已刪除聯絡人：{nickname}"
        return "❌ 找不到該聯絡人"

    def _save_to_file(self, db):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)