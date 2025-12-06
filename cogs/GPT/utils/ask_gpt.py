import os
import openai
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

API_KEY = os.getenv("GPT_API")

# 建立一個共用的函數來呼叫 GPT
def ask_gpt(messages, max_tokens=300):
    try:
        client = openai.OpenAI(
            api_key=API_KEY,
            base_url="https://free.v36.cm/v1/",
            default_headers={"x-foo": "true"}
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"發生錯誤：{str(e)}"