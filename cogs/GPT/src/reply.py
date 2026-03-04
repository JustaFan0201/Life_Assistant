import discord
from discord import app_commands
from discord.ext import commands
from ..utils.ask_gpt import ask_gpt

TARGET_CHANNEL_ID = 1476178479329312858

class ReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active = False
        self.history = [] # 存公開頻道的對話紀錄

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
        if self.active and message.channel.id == TARGET_CHANNEL_ID and message.author != self.bot.user:
            messages = []
            for q, a in self.history[-5:]:
                messages.append({"role": "user", "content": q})
                messages.append({"role": "assistant", "content": a})
            
            messages.append({"role": "user", "content": message.content})

            async with message.channel.typing():
                try:
                    result = ask_gpt(messages, max_tokens=500)
                    await message.channel.send(result)
                    self.history.append((message.content, result))
                except Exception as e:
                    print(f"GPT Error: {e}")
