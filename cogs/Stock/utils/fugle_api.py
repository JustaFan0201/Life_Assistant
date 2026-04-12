import requests

def get_stock_snapshot(symbol: str, api_token: str):
    """
    獲取單一股票的即時報價與基本資料
    """
    # 💡 關鍵 1：使用 intraday/quote 抓取價格，intraday/ticker 抓取名稱
    # 為了省事，我們直接合併邏輯。首先定義標頭
    headers = {
        "X-API-KEY": api_token  # 💡 2026 官方建議使用 X-API-KEY
    }
    
    base_url = "https://api.fugle.tw/marketdata/v1.0/stock/intraday"

    try:
        # A. 抓取基本資料 (為了拿到股票名稱)
        ticker_res = requests.get(f"{base_url}/ticker/{symbol}", headers=headers, timeout=5)
        # B. 抓取即時報價 (為了拿到成交價、漲跌幅)
        quote_res = requests.get(f"{base_url}/quote/{symbol}", headers=headers, timeout=5)

        if ticker_res.status_code == 200 and quote_res.status_code == 200:
            ticker_data = ticker_res.json()
            quote_data = quote_res.json()

            return {
                "name": ticker_data.get("name"),            # 從 ticker 拿名稱 (例如: 台積電)
                "price": quote_data.get("lastPrice"),       # 從 quote 拿最後成交價
                "change_pct": quote_data.get("changePercent"), # 拿漲跌幅
                "open": quote_data.get("openPrice")
            }
        else:
            print(f"Fugle API 錯誤: Ticker({ticker_res.status_code}), Quote({quote_res.status_code})")
            return None

    except Exception as e:
        print(f"API 請求異常: {e}")
        return None