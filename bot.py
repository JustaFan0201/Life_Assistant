import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import datetime

# 取得 bot.py 的所在目錄 
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
COGS_DIR = os.path.join(BASE_DIR, "cogs")

load_dotenv()  # 確保讀取的是 bot.py 同目錄
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)

# 當機器人完成啟動時
@bot.event
async def on_ready():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"目前登入身份 --> {bot.user}")
    channel_id = 1427945108019609640
    channel = bot.get_channel(channel_id)
    msg = f"Bot 已上線！現在時間：{now}"
    if channel:
        await channel.send(msg)
    else:
        print(f"找不到頻道 {channel_id}")

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
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"ReLoaded {extension} done.")

# 一開始bot開機需載入全部程式檔案
async def load_extensions():
    # 遍歷 cogs 資料夾下的所有項目
    for item in os.listdir(COGS_DIR):
        item_path = os.path.join(COGS_DIR, item)

        # 情況 1: 傳統的單一 .py 檔案 (例如 cogs/general.py)
        if os.path.isfile(item_path) and item.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{item[:-3]}")
                print(f"Loaded extension: cogs.{item[:-3]}")
            except Exception as e:
                print(f"Failed to load extension {item}: {e}")

        # 情況 2: 資料夾形式的專案 (例如 cogs/ticket/)
        elif os.path.isdir(item_path):
            if os.path.exists(os.path.join(item_path, "__init__.py")):
                # 如果有 __init__.py，直接載入資料夾名稱
                await bot.load_extension(f"cogs.{item}") 

async def main():
    async with bot:
        await load_extensions()
        keep_alive(local_test=True)  # 啟動保持存活的服務
        await bot.start(TOKEN)

# 確定執行此py檔才會執行
if __name__ == "__main__":
    asyncio.run(main())