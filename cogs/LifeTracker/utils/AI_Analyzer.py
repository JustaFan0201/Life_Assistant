# cogs\LifeTracker\utils\AI_Analyzer.py
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
    async def analyze_lifestyle(category_name, data_content):
        """
        使用 Nemotron 120B 進行週總結分析
        """
        prompt = f"""
        你是一位專業的生活導師。以下是使用者在「{category_name}」分類下的近期紀錄：
        {data_content}
        
        請進行客觀分析：
        1. 總結整體情況（約75字）。
        2. 具體行動建議（約75字）。
        使用繁體中文，總字數 150 字以內。
        """
        
        try:
            # 💡 參考範例：使用 chat.completions 
            response = await client.chat.completions.create(
                model=AI_Analyzer.MODEL_ID,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ OpenRouter 分析失敗: {e}")
            return "⚠️ 分析服務暫時不可用。"

    @staticmethod
    async def process_text_to_data(text: str, user_categories: list):
        """
        將 Whisper 轉出的文字傳給 Nemotron 轉換為 JSON
        """
        cat_context = "\n".join([
            f"- ID:{c['id']}, 名稱:{c['name']}, 欄位:{c['fields']}, 標籤:[{', '.join(c['subcats'])}]"
            for c in user_categories
        ])

        prompt = f"""
        你是一個只會輸出 JSON 的後端助手。請將文字歸納為 JSON。
        文字內容："{text}"
        可用分類：
        {cat_context}
        如果內容提到主分類，完全沒說到標籤或是與標籤的關聯性不高，就將標籤設定為NULL
        但如果文字有提到標籤相關內容並且文字形容上與主分類不同，就將尋找對應的標籤名稱填入subcat_name，否則設定為NULL。

        輸出格式範例：
        {{
            "category_id": int,
            "cat_name": "str",
            "subcat_name": "str",
            "values": {{ "欄位名": 數值 }},
            "note": "備註",
            "recognized_text": "{text}"
        }}
        """

        try:
            response = await client.chat.completions.create(
                model=AI_Analyzer.MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            res_text = response.choices[0].message.content.strip()
            res_text = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(res_text)
            
        except Exception as e:
            print(f"❌ Nemotron 解析數據錯誤: {e}")
            return None
        
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