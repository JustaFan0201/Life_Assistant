from datetime import datetime
from config import TW_TZ

MAX_MONTH_OFFSET = 12
TIMEOUT_VIEW_DEFAULT = 60

# 顯示與分頁設定 (Display & Pagination)
MAX_TEXT_LENGTH = 10
ITEMS_PER_PAGE = 10       # 清單每頁顯示的行程數量
MAX_DESC_PREVIEW_LEN = 25 # 行程內容在清單預覽時的最高字數 (超過會加...)
LIST_DESC_PREVIEW_LEN = 15

ADD_YEAR_RANGE = 1 # 新增行程時，年份選項的範圍 (從今年開始往後幾年)
# 標籤與 Emoji 映射 (Labels & Emojis)
PRIORITY_MAP = {
    "0": "🔴", # 緊急 / 高優先級
    "1": "🟡", # 重要 / 中優先級
    "2": "🟢"  # 普通 / 低優先級
}

PRIVACY_MAP = {
    True: "🔒", # 私人行程 (is_private=True)
    False: "🌍" # 公開行程 (is_private=False)
}

def get_max_month_offset() -> int:
    """
    💡 動態計算最大月份偏移量 (到明年12月)
    因為時間是流動的，所以必須用函式來確保每次取得的都是「當下的時間」。
    """
    now = datetime.now(TW_TZ)
    return 24 - now.month