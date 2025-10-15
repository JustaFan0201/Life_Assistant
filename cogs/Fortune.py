import discord
from discord import app_commands
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)
api_key = os.getenv("GPT_API")
# 定義名為 Main 的 Cog
class Fortune(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 關鍵字觸發
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print(f"{__name__} loaded successfully")

    # 前綴指令
    @app_commands.command(name="fortune", description="check your fortune for today.")
    async def fortune(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = "請以簡短有趣的方式，隨機生成一則今日運勢，給予一些建議做的事與不建議做的事情。"
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://free.v36.cm/v1/",
                default_headers={"x-foo": "true"}
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            result = response.choices[0].message.content.strip()
            await interaction.followup.send(f"{result}")
        except Exception as e:
            await interaction.followup.send(f"查詢失敗：{e}")

# Cog 載入 Bot 中
async def setup(bot):
    await bot.add_cog(Fortune(bot))