import discord
from discord import app_commands
from discord.ext import commands
from ..utils import ask_gpt

TARGET_CHANNEL_ID = 1423551561187070022

class ReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.history = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Reply Module loaded.")

    @app_commands.command(name="set_reply", description="設定自動回覆功能開關")
    async def set_reply(self, interaction: discord.Interaction, status: bool):
        self.active = status
        await interaction.response.send_message(f"自動回覆功能已{'開啟' if status else '關閉'}。")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 檢查開關是否開啟、是否在指定頻道、是否為機器人自己
        if self.active and message.channel.id == TARGET_CHANNEL_ID and message.author != self.bot.user:
            
            # 建立歷史訊息串列 (取最近 5 組)
            messages = []
            for q, a in self.history[-5:]:
                messages.append({"role": "user", "content": q})
                messages.append({"role": "assistant", "content": a})
            
            # 加入當前使用者的訊息
            messages.append({"role": "user", "content": message.content})

            # 顯示「正在輸入...」的狀態，讓使用者知道機器人正在思考
            async with message.channel.typing():
                # 呼叫 utils 裡的函數
                result = ask_gpt(messages, max_tokens=500)
            
            await message.channel.send(result)
            
            # 儲存本次問答到歷史紀錄
            self.history.append((message.content, result))