import os
import asyncio
import discord
from discord.ext import commands
from keep_alive import keep_alive
import datetime
from database.db import init_db, SessionLocal
from database.models import BotSettings
from cogs.System.settings import get_botsettings

from config import COGS_DIR, DISCORD_BOT_TOKEN, RENDER

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)
bot.db_session = SessionLocal

@bot.event
async def on_ready():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"目前登入身份 --> {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"成功同步 {len(synced)} 個斜線指令！")
    except Exception as e:
        print(f"同步斜線指令失敗: {e}")

    notify_channel_id = None
    
    notify_channel_id = get_botsettings(BotSettings.login_notify_channel_id)
    if notify_channel_id: 
        print(f"🔍 從資料庫讀取到通知頻道 ID: {notify_channel_id}")
        try:
            target_id = int(notify_channel_id)
            channel = await bot.fetch_channel(target_id)
            
            msg = f"🟢 **Bot 已上線！**\n時間：`{now}`"
            await channel.send(msg)
            print(f"✅ 上線通知已發送至頻道: {channel.name} (ID: {channel.id})")
            
        except ValueError:
            print(f"❌ 通知失敗：ID '{notify_channel_id}' 不是有效的數字。")
        except discord.NotFound:
            print(f"❌ 通知失敗：找不到頻道 ID {notify_channel_id} (請確認 ID 正確且機器人在該伺服器)。")
        except discord.Forbidden:
            print(f"❌ 通知失敗：機器人沒有權限在該頻道發言。")
        except Exception as e:
            print(f"❌ 通知發送發生未知錯誤: {e}")
    else:
        print("⚠️ 尚未設定 Login_Notify_Channel_ID (請使用 /set_login_notify_channel 設定)。")

# 載入指令程式檔案
@bot.command()
async def load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.")

# 卸載指令檔案
@bot.command()
async def unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"UnLoaded {extension} done.")

# 重新載入程式檔案
@bot.command()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f"cogs.{extension}")
        # 重新同步指令清單
        await bot.tree.sync()
        await ctx.send(f"ReLoaded {extension} and synced commands.")
    except Exception as e:
        await ctx.send(f"Error reloading {extension}: {e}")

# 一開始bot開機需載入全部程式檔案
async def load_extensions():
    # 遍歷 cogs 資料夾下的所有項目
    if not os.path.exists(COGS_DIR):
        print(f"⚠️ 找不到 cogs 資料夾：{COGS_DIR}")
        return

    for item in os.listdir(COGS_DIR):
        item_path = os.path.join(COGS_DIR, item)
        # 開始遍歷
        if os.path.isdir(item_path):
            if os.path.exists(os.path.join(item_path, "__init__.py")):
                # 如果有 __init__.py，直接載入資料夾名稱
                try:
                    await bot.load_extension(f"cogs.{item}")
                    print(f"已載入模組: cogs.{item}")
                except Exception as e:
                    print(f"❌ 載入模組失敗 cogs.{item}: {e}")

async def main():
    print("script start.")
    async with bot:
        await load_extensions()
        keep_alive(local_test=not RENDER)
        
        if DISCORD_BOT_TOKEN:
            print("get token and try to start bot.")
            await bot.start(DISCORD_BOT_TOKEN)
        else:
            print("❌ 錯誤：未讀取到 DISCORD_BOT_TOKEN，請檢查 .env 檔案")

# 確定執行此py檔才會執行
if __name__ == "__main__":
    try:
        if init_db():
            asyncio.run(main())
            pass
        else:
            print("Error: Database connection failed. Program will stop.")
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
        pass