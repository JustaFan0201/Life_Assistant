# cogs\LifeTracker\utils\AI_Analyzer.py
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class AI_Analyzer:
    SUMMARY_MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free"
    
    CLASSIFY_MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"

    @staticmethod
    async def analyze_lifestyle(category_name, data_content):
        """
        使用大模型進行週總結分析
        """
        # 防呆機制：如果本週完全沒有紀錄，直接回傳預設字串，不要浪費資源問 AI
        if not data_content or str(data_content).strip() in ["", "[]", "None"]:
            return "本週尚無相關紀錄，繼續保持追蹤習慣喔！"

        prompt = f"""
        你是一位專業的生活導師。以下是使用者在「{category_name}」分類下的近期紀錄：
        {data_content}
        
        請進行客觀分析：
        1. 總結整體情況（約75字）。
        2. 具體行動建議（約75字）。
        使用繁體中文，總字數 150 字以內。
        """
        
        try:
            response = await client.chat.completions.create(
                model=AI_Analyzer.SUMMARY_MODEL_ID,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                timeout=180.0
            )
            
            # 安全取值防護：避免 OpenRouter 伺服器異常回傳 None 導致崩潰
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
                return content.strip() if content else "⚠️ AI 未回傳分析結果。"
            else:
                return "⚠️ 分析服務目前忙線中，回傳格式異常。"
                
        except Exception as e:
            print(f"❌ OpenRouter 分析失敗: {e}")
            return "⚠️ 分析服務暫時不可用。"

    @staticmethod
    async def classify_consumption(item_name: str, subcat_list: list):
        """
        使用小模型進行快速消費分類
        """
        if not subcat_list: return "其他"
        
        # 🌟 同樣加上空值防護
        if not item_name or str(item_name).strip() == "": 
            return "其他"

        prompt = f"""
        你是一位消費紀錄分類專家。
        使用者購買了：『{item_name}』
        請從以下現有的標籤清單中，選擇一個最適合的分類：
        清單：{", ".join(subcat_list)}
        
        請直接回覆該標籤名稱即可，不要有任何多餘的解釋或標點符號。
        如果真的都不適合，請回覆「其他」。
        """
        
        try:
            response = await client.chat.completions.create(
                model=AI_Analyzer.CLASSIFY_MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # 🌟 分類模型也加上安全取值防護
            if hasattr(response, 'choices') and response.choices:
                result = response.choices[0].message.content
                if result:
                    result = result.strip()
                    return result if result in subcat_list else "其他"
            
            return "其他"
        except Exception as e:
            print(f"❌ AI 分類失敗: {e}")
            return "其他"