from discord.ext import commands
from datetime import time
from cogs.VoiceSensor.ActionHandler import ActionHandler
from cogs.VoiceSensor.utils import AI_Analyzer
from cogs.VoiceSensor.src import stt_whisper
from config import TW_TZ
REPORT_TIME = time(hour=0, minute=0, tzinfo=TW_TZ)

class VoiceSensorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_handler = ActionHandler(bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # 🎤 === 語音訊息 ===
        if message.flags.voice and message.attachments:
            voice_file = message.attachments[0]
            processing_msg = await message.reply("🎙️ 正在處理您的語音指令...")

            try:
                audio_data = await voice_file.read()

                try:
                    await message.delete()
                except:
                    pass

                # 👉 語音轉文字
                recognized_text = stt_whisper(audio_data)

                if not recognized_text.strip():
                    return await processing_msg.edit(content="❌ 沒聽清楚您說什麼")

                # ✅ 共用流程
                await self.process_text(recognized_text, message, processing_msg)

            except Exception as e:
                await processing_msg.edit(content=f"❌ 語音失敗：{e}")

        # 💬 === 新增：一般文字（非指令） ===
        elif not message.content.startswith(self.bot.command_prefix):
            processing_msg = await message.reply("🧠 處理中...")

            try:
                # ✅ 共用流程
                await self.process_text(message.content, message, processing_msg)
            except Exception as e:
                await processing_msg.edit(content=f"❌ 處理失敗：{e}")

        # ⚠️ 一定要加（不然指令會壞掉）
        await self.bot.process_commands(message)


    async def process_text(self, text: str, message, processing_msg):
        # 1️⃣ 呼叫 AI
        result = await AI_Analyzer.parse_ui_action(text)

        actions = result.get("actions", [])

        if not actions:
            return await processing_msg.edit(content="❌ 無法解析操作")

        await self.action_handler.handle_actions(message, processing_msg, actions)