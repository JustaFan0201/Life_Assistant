import json
import os
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, COGS_DIR

# 初始化 OpenRouter 客戶端
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

PROMPT_PATH = os.path.join(COGS_DIR, "VoiceSensor", "utils", "prompt.txt")
prompt = ""
with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
    prompt = f.read() 

class AI_Analyzer:
    MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"
    #MODEL_ID = "nvidia/nemotron-3-nano-30b-a3b:free"
    @staticmethod
    async def parse_ui_action(text: str):
        """
        判斷使用者的語音意圖
        """
        print("開始分析文字意圖")
        content = prompt + "\n\n使用者文字為:\n" + text

        try:
            response = await client.chat.completions.create(
                model=AI_Analyzer.MODEL_ID,
                messages=[{"role": "user", "content": content}],
                response_format={ "type": "json_object" }
            )
            print("分析json的結果:")
            print(response.choices[0].message.content.strip())
            return json.loads(response.choices[0].message.content.strip())
        except:
            return {"intent": "CHAT"}