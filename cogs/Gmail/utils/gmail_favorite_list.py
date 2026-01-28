import os
import json
import re

class EmailFavoriteList:
    def __init__(self, folder_path):
        self.file_path = os.path.join(folder_path, "email_list.json")
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
        
    def add_and_save(self, email):
        db = self.read_db()

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email) is None:
            return "❌ email 格式不符"

        if any(item['email'] == email for item in db["data"]):
            return "⚠️ 該 Email 已在列表中，無需重複添加"

        new_data = {"email": email}
        db["data"].append(new_data)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
            return f"✅ 成功新增：{email}"
        except Exception as e:
            print(f"寫入檔案失敗: {e}")
            return "❌ 寫入檔案失敗，請通知管理員"
        
    