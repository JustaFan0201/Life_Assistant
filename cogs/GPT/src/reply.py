import discord
from discord.ext import commands
from cogs.GPT.utils.ask_gpt import ask_gpt
from cogs.GPT.src.memory_manager import MemoryManager
from database.models import BotSettings
from database.db_utils import get_botsettings
from collections import deque
from database.db import SessionLocal

class ReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.memory_manager = MemoryManager()
        self.history = deque(maxlen=10) # 存公開頻道的對話紀錄

    @commands.Cog.listener()
    async def on_ready(self):
        print("[GPT] Reply Module loaded.")

    async def process_direct_chat(self, interaction: discord.Interaction, user_message: str):
        """處理來自 Modal 的單次提問"""
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True) # ephemeral=True 只有該使用者看得到

        # 這裡我們不使用 self.history，因為這是私密/單次的問答
        messages = [{"role": "user", "content": user_message}]

        try:
            result = ask_gpt(messages, max_tokens=500)
            await interaction.followup.send(f"**你問：** {user_message}\n\n**GPT 回：**\n{result}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 發生錯誤: {e}", ephemeral=True)

    async def toggle_active_status(self, interaction: discord.Interaction):
        self.active = not self.active
        status_text = "🟢 開啟" if self.active else "🔴 關閉"
        await interaction.response.send_message(f"自動回覆功能已切換為：{status_text}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.author.bot: return
        user_id = message.author_id
        msg_text = message.content
        metadata = {"guild_name": message.guild.name,
                    "channel_name": message.channel.name}
        
        with SessionLocal() as db:
            if self.active and (message.guild or message.channel.id == get_botsettings(BotSettings.gpt_channel_id, db, message.guild.id)):
                # can talk
                messages = []
                
                mems = self.memory_manager.search_memory(user_id, msg_text, k=3, db=db)
                mems_text = "\n".join(m["text"] for m in mems)
                for m in mems:
                    self.m
                if mems_text:
                    messages.append({
                        "role": "system",
                        "content": f"以下是與對話相關的記憶：\n{mems_text}"
                    })
                
                for q, a in self.history:
                    messages.append({"role": "user", "content": q})
                    messages.append({"role": "assistant", "content": a})
                
                messages.append({"role": "user", "content": message.content})

                async with message.channel.typing():
                    try:
                        result = ask_gpt(messages, max_tokens=500)
                        await message.channel.send(result)
                        self.history.append((message.content, result))
                        self.memory_manager.add_memory(user_id, msg_text, metadata)
                    except Exception as e:
                        print(f"GPT Error: {e}")
            else:
                self.memory_manager.add_memory(user_id, msg_text, metadata)
            
