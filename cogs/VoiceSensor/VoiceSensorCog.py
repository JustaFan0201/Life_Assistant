import discord
from discord.ext import commands
from datetime import time
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.VoiceSensor.utils import AI_Analyzer
from cogs.VoiceSensor.src import stt_whisper
from config import TW_TZ
REPORT_TIME = time(hour=0, minute=0, tzinfo=TW_TZ)

class VoiceSensorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


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
                await self.process_text(message, recognized_text, processing_msg)

            except Exception as e:
                await processing_msg.edit(content=f"❌ 語音失敗：{e}")

        # 💬 === 新增：一般文字（非指令） ===
        elif not message.content.startswith(self.bot.command_prefix):
            processing_msg = await message.reply("🧠 處理中...")

            try:
                # ✅ 共用流程
                await self.process_text(message, message.content, processing_msg)
            except Exception as e:
                await processing_msg.edit(content=f"❌ 處理失敗：{e}")

        # ⚠️ 一定要加（不然指令會壞掉）
        await self.bot.process_commands(message)


    async def process_text(self, message, text: str, processing_msg):
        # --- 1. 準備上下文 ---
        raw_cats = LifeTracker_Manager.get_user_categories(message.author.id)

        all_labels = []
        full_context_cats = []

        for cat in raw_cats:
            _, subcats = LifeTracker_Manager.get_category_details(cat.id)

            all_labels.append(cat.name)
            sub_names = [s['name'] for s in subcats]

            all_labels.extend(sub_names)

            full_context_cats.append({
                "id": cat.id,
                "name": cat.name,
                "fields": cat.fields,
                "subcats": sub_names
            })

        
        # --- 2. 意圖判斷 ---
        intent_data = await AI_Analyzer.classify_intent(text)
        intent = intent_data.get("intent", "CHAT")

        # --- 3. 分流 ---
        if intent == "RECORD":
            await processing_msg.edit(content=f"📌 紀錄：{text}")

        elif intent == "QUERY":
            await processing_msg.edit(content="📊 這是您的個人看板")

        elif intent == "MANAGE":
            await processing_msg.edit(content="⚙️ 管理需求")

        else:
            await processing_msg.edit(
                content=f"🤖 我聽到了：『{text}』\n但我還不確定怎麼處理"
            )