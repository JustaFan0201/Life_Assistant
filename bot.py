import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import datetime
from database.db import init_db, DatabaseSession
from database.models import BotSettings

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
COGS_DIR = os.path.join(BASE_DIR, "cogs")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NOTIFY_CHANNEL_ID = os.getenv("Login_Notify_Channel_ID")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)

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
    
    try:
        with DatabaseSession() as db:
            settings = db.query(BotSettings).filter(BotSettings.id == 1).first()
            if settings and settings.login_notify_channel_id:
                notify_channel_id = settings.login_notify_channel_id
                print(f"🔍 從資料庫讀取到通知頻道 ID: {notify_channel_id}")
    except Exception as e:
        print(f"❌ 讀取資料庫設定失敗: {e}")

    if notify_channel_id:
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

        # 情況 1: 傳統的單一 .py 檔案 (例如 cogs/general.py)
        '''if os.path.isfile(item_path) and item.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{item[:-3]}")
                print(f"Loaded extension: cogs.{item[:-3]}")
            except Exception as e:
                print(f"Failed to load extension {item}: {e}")'''

        # 情況 2: 資料夾形式的專案 (例如 cogs/ticket/)
        if os.path.isdir(item_path):
            if os.path.exists(os.path.join(item_path, "__init__.py")):
                # 如果有 __init__.py，直接載入資料夾名稱
                try:
                    await bot.load_extension(f"cogs.{item}")
                    print(f"已載入模組: cogs.{item}")
                except Exception as e:
                    print(f"❌ 載入模組失敗 cogs.{item}: {e}")

async def main():
    async with bot:
        await load_extensions()
        if os.getenv("RENDER"):
            keep_alive(local_test=False)
        else:
            keep_alive(local_test=True)
        
        if TOKEN:
            await bot.start(TOKEN)
        else:
            print("❌ 錯誤：未讀取到 DISCORD_BOT_TOKEN，請檢查 .env 檔案")

# 確定執行此py檔才會執行
if __name__ == "__main__":
    try:
        init_db()
        asyncio.run(main())
    except KeyboardInterrupt:
        pass