import openai
from config import GPT_API

# 建立一個共用的函數來呼叫 GPT
def ask_gpt(messages, max_tokens=300):
    try:
        client = openai.OpenAI(
            api_key=GPT_API,
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