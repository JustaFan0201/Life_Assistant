# cogs\LifeTracker\utils\AI_Analyzer.py
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class AI_Analyzer:
    # 💡 [模型路由設定] 為不同任務指派最適合的模型
    # 1. 總結專用模型 (負責長文推理，使用較聰明的大模型)
    SUMMARY_MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free"
    
    # 2. 分類專用模型 (負責簡單比對，使用速度極快的小模型)
    CLASSIFY_MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"

    @staticmethod
    async def analyze_lifestyle(category_name, data_content):
        """
        使用大模型進行週總結分析
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
            response = await client.chat.completions.create(
                model=AI_Analyzer.SUMMARY_MODEL_ID,  # 🌟 這裡呼叫總結模型
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ OpenRouter 分析失敗: {e}")
            return "⚠️ 分析服務暫時不可用。"

    @staticmethod
    async def classify_consumption(item_name: str, subcat_list: list):
        """
        使用小模型進行快速消費分類
        item_name: 商品品名 (如: 飲冰室茶集紅奶茶)
        subcat_list: 目前資料庫中有的子分類名稱清單 (如: ['飲料', '食物', '生活用品'])
        """
        if not subcat_list: return "其他"

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
            result = response.choices[0].message.content.strip()
            return result if result in subcat_list else "其他"
        except Exception as e:
            print(f"❌ AI 分類失敗: {e}")
            return "其他"