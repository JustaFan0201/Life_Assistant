import json
import os
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY

# 初始化 OpenRouter 客戶端
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class AI_Analyzer:
    MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"
    #MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"
    @staticmethod
    async def classify_intent(text: str):
        """
        判斷使用者的語音意圖
        """
        prompt = f"""
        你是一位助理。請分析以下文字的意圖，並回傳 JSON。
        文字："{text}"
        
        可能的意圖：
        1. "RECORD": 使用者想要記錄數據（例如：我吃了午餐、運動了半小時）。
        2. "QUERY": 使用者想要查詢資料（例如：我這週喝了多少水、顯示看板）。
        3. "MANAGE": 使用者想要管理設定（例如：幫我新增一個分類、刪除區間）。
        4. "CHAT": 純粹聊天或無意義內容。

        輸出格式：{{"intent": "str", "reason": "str"}}
        """
        try:
            response = await client.chat.completions.create(
                model=AI_Analyzer.MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content.strip())
        except:
            return {"intent": "CHAT"}