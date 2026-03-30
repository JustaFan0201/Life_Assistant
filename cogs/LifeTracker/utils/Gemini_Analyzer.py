from google import genai
import os
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

class GeminiAnalyzer:
    @staticmethod
    async def analyze_lifestyle(category_name, data_content):
        model_id = "gemini-2.5-flash" 
        
        prompt = f"""
        你是一位專業的生活導師與數據分析專家。以下是使用者在「{category_name}」分類下的近期紀錄：
        
        {data_content}
        
        請根據以上資料進行客觀分析：
        1. 總結這段時間的整體情況。75字左右。
        2. 具體的行動建議。75字左右。
        
        請使用「繁體中文」，客觀冷靜的回答不帶情緒，總字數控制在 150 字以內。
        """
        
        try:
            response = await client.aio.models.generate_content(
                model=model_id,
                contents=prompt
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini AI 分析發生錯誤: {e}")
            return "⚠️ AI 分析暫時無法使用，請稍後再試。"