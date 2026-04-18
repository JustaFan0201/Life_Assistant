from datetime import timedelta, timezone, time

# 時區與時間設定
TW_TIME = timezone(timedelta(hours=8))
MARKET_OPEN = 900   # 09:00
MARKET_CLOSE = 1335 # 13:35
REPORT_TIME = time(hour=13, minute=45, tzinfo=TW_TIME)

# 交易成本設定 (手續費 0.1425% * 0.6折扣 + 證交稅 0.3%)
FEE_RATE = 0.001425 * 0.6
TAX_RATE = 0.003
TOTAL_SELL_COST_RATE = FEE_RATE + TAX_RATE