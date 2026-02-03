import os
import json
import re

class EmailFavoriteList:
    def __init__(self, folder_path):
        self.file_path = os.path.join(folder_path, "email_list.json")
        self.template = {"data": {}}

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

        # 4. 儲存
        db["data"][uid][name] = email

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
            return f"✅ 成功新增聯絡人：{name} ({email})"
        except Exception as e:
            return f"❌ 寫入失敗: {e}"
        
    