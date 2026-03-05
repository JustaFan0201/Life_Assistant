import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from database.db import engine
from database.models import Base

def drop_all_tables():
    print("==================================================")
    print("⚠️ 警告：這將會刪除資料庫中的「所有資料表」與「所有資料」！")
    print("==================================================")
    
    confirm = input("確定要繼續嗎？(請輸入 'y' 或 'yes' 確認執行): ")
    
    if confirm.lower() in ['y', 'yes']:
        try:
            # 刪除 Base 中定義的所有資料表
            Base.metadata.drop_all(bind=engine)
            print("\n🗑️ [成功] 所有資料表已成功刪除！")
            print("💡 提示：你可以重新啟動機器人，或是執行 init_db() 來重新建立乾淨的資料表。")
        except Exception as e:
            print(f"\n❌ [錯誤] 刪除資料表時發生錯誤：{e}")
    else:
        print("\n❌ [取消] 已取消操作，資料庫未被修改。")

if __name__ == "__main__":
    drop_all_tables()