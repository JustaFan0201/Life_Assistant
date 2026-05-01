import json
import re
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class Gmail_AI_Analyzer:
    # 處理信件需要較強的閱讀理解與 JSON 格式輸出能力，建議使用大模型
    MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free" 

    @staticmethod
    async def analyze_and_classify_email(subject: str, body: str, categories: list[dict]) -> tuple[str, str]:
        """
        分析信件並同時給出「分類」與「20字摘要」。
        categories 格式預期為: [{"name": "繳費", "desc": "包含水電、瓦斯等帳單"}, ...]
        
        回傳: (category_name, summary)
        如果分類失敗，category_name 會回傳 None
        """
        # 如果使用者完全沒有設定分類，我們就只要摘要就好
        if not categories:
            categories_prompt = "目前沒有任何分類。請在 category 欄位回傳 null。"
        else:
            cat_list_str = "\n".join([f"- 【{c['name']}】: {c['desc']}" for c in categories])
            categories_prompt = f"請從以下分類中挑選最適合的一個（必須完全符合名稱）。如果都不適合，請在 category 欄位回傳 null。\n現有分類：\n{cat_list_str}"

        prompt = f"""
        你是一位專業的企業級秘書。請閱讀以下使用者的最新電子郵件，並完成分類與摘要任務。
        
        【信件主旨】: {subject}
        【信件內文】: {body}
        
        【任務說明】
        1. 分類：{categories_prompt}
        2. 摘要：請為這封信件撰寫一段極度精簡的繁體中文摘要，絕對不能超過 20 個字。
        
        【輸出限制】
        你必須「只」輸出一段合法的 JSON 字串，不要有任何 Markdown 標記 (如 ```json) 也不要有其他解釋文字。格式如下：
        {{
            "category": "分類名稱或 null",
            "summary": "你的20字內摘要"
        }}
        """
        
        try:
            response = await client.chat.completions.create(
                model=Gmail_AI_Analyzer.MODEL_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1 # 溫度調低，確保 AI 乖乖輸出 JSON
            )
            
            raw_result = response.choices[0].message.content.strip()
            
            clean_json_str = re.sub(r"```json\n?|\n?```", "", raw_result).strip()
            
            parsed_data = json.loads(clean_json_str)
            
            category_name = parsed_data.get("category")
            summary = parsed_data.get("summary", "（無法生成摘要）")
            
            valid_category_names = [c["name"] for c in categories]
            if category_name not in valid_category_names:
                category_name = None
                
            return category_name, summary

        except json.JSONDecodeError as e:
            print(f"❌ AI 回傳的 JSON 格式解析失敗: {e}\n原始回傳: {raw_result}")
            return None, "（AI 摘要解析失敗）"
        except Exception as e:
            print(f"❌ Gmail AI 分析失敗: {e}")
            return None, "（AI 分析服務暫時不可用）"