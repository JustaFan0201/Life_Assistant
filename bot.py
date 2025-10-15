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
    for filename in os.listdir(COGS_DIR): 
        if filename.endswith(".py"): 
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load_extensions()
        keep_alive()
        await bot.start(TOKEN)

# 確定執行此py檔才會執行
if __name__ == "__main__":
    asyncio.run(main())