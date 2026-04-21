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
