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
        if message.author.bot: return
        
        if message.flags.voice and message.attachments:
            voice_file = message.attachments[0]
            processing_msg = await message.reply("🎙️ 正在處理您的語音指令...")
            
            try:
                audio_data = await voice_file.read()
                try:
                    await message.delete()
                except discord.Forbidden:
                    # 如果機器人沒有「管理訊息」的權限，刪除會失敗，這裡做個防呆
                    print("⚠️ 機器人權限不足，無法刪除語音訊息。")
                except discord.NotFound:
                    # 訊息可能已經被使用者手動刪除
                    pass
                # --- 1. 準備 Whisper 暗示與 AI 上下文 ---
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

                whisper_prompt = ", ".join(set(all_labels)) 

                # --- 2. 語音轉文字 ---
                recognized_text = stt_whisper(audio_data, prompt_text=whisper_prompt)
                if not recognized_text.strip():
                    return await processing_msg.edit(content="❌ 沒聽清楚您說什麼，請再試一次。")

                # --- 3. AI 意圖識別 ---
                # 這裡調用我們之前討論過的 classify_intent 方法
                intent_data = await AI_Analyzer.classify_intent(recognized_text)
                intent = intent_data.get("intent", "CHAT")

                # --- 4. 根據意圖分發功能 ---
                
                # 意圖 A: 數據記錄
                if intent == "RECORD":
                    result = await processing_msg.edit(content="紀錄")

                    '''result = await AI_Analyzer.process_text_to_data(recognized_text, full_context_cats)
                    
                    if result and "category_id" in result:
                        # 💡 執行資料庫寫入 (從 AI 回傳結果中尋找對應 subcat_id)
                        # 注意：這裡需要你的 Manager 有一個根據名稱找 ID 的輔助方法
                        success = LifeTracker_Manager.add_voice_record(message.author.id, result)
                        
                        if success:
                            await processing_msg.edit(
                                content=f"✅ **已為您紀錄！**\n"
                                        f"分類：**{result['cat_name']}** | 標籤：**{result['subcat_name']}**\n"
                                        f"內容：`{result['recognized_text']}`"
                            )
                        else:
                            await processing_msg.edit(content="❌ 資料存入失敗，請檢查分類或標籤設定。")
                    else:
                        await processing_msg.edit(content="❌ AI 無法解析這筆紀錄的數據。")'''

                # 意圖 B: 顯示看板
                elif intent == "QUERY":
                    await processing_msg.edit(content="📊 這是您的個人看板")

                # 意圖 C: 管理需求
                elif intent == "MANAGE":
                    await processing_msg.edit(content="⚙️ 偵測到管理需求，請問您是想管理標籤還是分類？（請配合按鈕操作）")
                    # 這裡可以接 ManageSubcatView 等...

                # 意圖 D: 純聊天或無法識別
                else:
                    await processing_msg.edit(content=f"🤖 我聽到了：『{recognized_text}』\n目前我還不確定如何執行這個指令，您可以試著說「紀錄喝水」或「打開看板」。")

            except Exception as e:
                import traceback
                traceback.print_exc()
                await processing_msg.edit(content=f"❌ 語音指令執行失敗：{e}")