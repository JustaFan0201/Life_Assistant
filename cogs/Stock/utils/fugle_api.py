import requests
import logging

logger = logging.getLogger(__name__)

def get_stock_quote(symbol: str, token: str) -> dict:
    """
    富果行情 API V1.0 正式版 (已驗證)
    """
    if not token or not symbol:
        return {}

    clean_token = token.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    
    symbol = symbol.strip().upper()
    url = f"https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{symbol}"
    headers = {
        "X-API-KEY": clean_token,
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # 回傳給 Cog 顯示的欄位
            return {
                "symbol": data.get('symbol'),
                "name": data.get('name', '未知'),
                "lastPrice": data.get('lastPrice'),
                "changePercent": data.get('changePercent', 0),
                "change": data.get('change', 0)
            }
        else:
            logger.error(f"❌ API 失敗 ({response.status_code}): {response.text}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ 請求異常: {e}")
        return {}