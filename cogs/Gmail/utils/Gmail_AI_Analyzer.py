import json
import re
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY
import asyncio
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class Gmail_AI_Analyzer:
    MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free" 

    @staticmethod
    async def analyze_and_classify_email(subject: str, body: str, categories: list[dict]) -> tuple[str, str]:
        raw_result = "（無回傳內容）"
        
        if not categories:
            categories_prompt = "目前沒有任何分類。請在 category 欄位回傳 null。"
        else:
            cat_list_str = "\n".join([f"- {c['name']} (判斷規則: {c['desc']})" for c in categories])
            categories_prompt = f"請從以下分類中挑選最適合的一個（必須完全符合名稱，絕對不要加上任何括號）。如果都不適合，請在 category 欄位回傳 null。\n現有分類：\n{cat_list_str}"

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
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=Gmail_AI_Analyzer.MODEL_ID,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                ),
                timeout=60.0
            )
            
            if not hasattr(response, 'choices') or not response.choices:
                print(f"❌ [API 異常] OpenRouter 回傳了無效的格式")
                return None, "（API 回傳異常）"
                
            message = response.choices[0].message
            if not message or not message.content:
                print(f"❌ [API 異常] AI 回傳了空內容")
                return None, "（AI 回傳空內容）"
            
            raw_result = message.content.strip()
            print(f"🤖 [AI 原始回覆]:\n{raw_result}")
            
            clean_json_str = re.sub(r"```json\n?|\n?```", "", raw_result).strip()
            parsed_data = json.loads(clean_json_str)
            
            category_name = parsed_data.get("category")
            summary = parsed_data.get("summary", "（無法生成摘要）")
            
            if isinstance(category_name, str):
                category_name = category_name.strip("【】「」[]'\" ")
            
            valid_category_names = [c["name"] for c in categories]
            if category_name not in valid_category_names:
                category_name = None
                
            print(f"💡 [解析結果] 最終分類: {category_name} | 摘要: {summary}")
            return category_name, summary

        except asyncio.TimeoutError:
            print(f"⏱️ [AI 超時] 分析信件 '{subject}' 時反應過慢，已跳過。")
            return None, "（AI 分析超時）"
        except json.JSONDecodeError:
            print(f"❌ [格式錯誤] AI 回傳內容非標準 JSON: {raw_result}")
            return None, "（摘要解析失敗）"
        except Exception as e:
            # 加上詳細錯誤追蹤，未來如果還有其他錯誤能看得很清楚
            import traceback
            traceback.print_exc()
            print(f"❌ [AI 錯誤] 分析失敗: {e}")
            return None, "（AI 暫時無法連線）"