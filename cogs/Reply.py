import discord
from discord import app_commands
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)
api_key = os.getenv("GPT_API")
CHANNEL_ID = 1423551561187070022  # 指定頻道 ID

class Reply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.history = []  # 儲存問答歷史

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print(f"{__name__} loaded successfully")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.active and message.channel.id == CHANNEL_ID and message.author != self.bot.user:
    
            # 建立歷史訊息串列
            messages = []
            for q, a in self.history[-5:]:  # 只取最近5組問答
                messages.append({"role": "user", "content": q})
                messages.append({"role": "assistant", "content": a})
            messages.append({"role": "user", "content": message.content})

            try:
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://free.v36.cm/v1/",
                    default_headers={"x-foo": "true"}
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=500
                )
                result = response.choices[0].message.content.strip()
                await message.channel.send(result)
                # 儲存本次問答
                self.history.append((message.content, result))
            except Exception as e:
                await message.channel.send(f"查詢失敗：{e}")

    @app_commands.command(name="set_reply", description="設定自動回覆功能開關 (true/false)")
    @app_commands.describe(status="true 或 false")
    async def set_reply(self, interaction: discord.Interaction, status: bool):
        self.active = status
        await interaction.response.send_message(f"自動回覆功能已設定為：{status}")

# Cog 載入 Bot 中
async def setup(bot):
    await bot.add_cog(Reply(bot))