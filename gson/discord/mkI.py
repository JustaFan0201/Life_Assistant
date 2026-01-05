import os
import asyncio
import discord
import json
from discord.ext import commands


script_dir = os.path.dirname(os.path.abspath(__file__))
COGS_DIR = os.path.join(script_dir, "cogs") 
CONFIG_FILE = "data.json" 
file_path = os.path.join(script_dir, CONFIG_FILE)

token = None
config_data = {}

try:
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        config_data = json.load(file)
    
    token = config_data.get("token")
    
    if token:
        token = token.strip()
        print("Token 讀取成功。")
    else:
        print(f"錯誤:JSON 檔案 '{CONFIG_FILE}' 中找不到 'token' 鍵。")

except FileNotFoundError:
    print(f"錯誤:找不到 {CONFIG_FILE} 檔案。")
except Exception as e:
    print(f"Token 讀取時發生未知錯誤: {e}")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix = "-", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot 成功登入為 {bot.user}')


@bot.command()
async def synccommands(ctx):

    if ctx.author.id == bot.owner_id or await bot.is_owner(ctx.author):
        synced = await bot.tree.sync(guild=ctx.guild)
        
        await ctx.send(f"斜線指令已成功同步 **{len(synced)}** 個到公會 **{ctx.guild.name}")
    else:
        await ctx.send("你沒有權限執行此指令。")


# @bot.command()
# async def checkServerID(ctx):
#     sever_id = ctx.guild.id
#     await ctx.send(sever_id)

@bot.hybrid_command()
async def ping(ctx):
    await ctx.send(f"Pong! 延遲：{round(bot.latency * 1000)}ms")


async def setup_hook():
    if not os.path.exists(COGS_DIR):
        print(f"找不到 cogs 資料夾 ({COGS_DIR})")
        return

    for filename in os.listdir(COGS_DIR): 
        if filename.endswith(".py"): 
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"成功載入 Cog：{filename[:-3]}")
            except Exception as e:
                print(f"載入 Cog 失敗：{filename[:-3]}")
                print(f"   錯誤訊息：{e}")

async def main():
    if not token:
        print("Bot Token 遺失。")
        return
        
    async with bot:
        bot.setup_hook = setup_hook
        #await load_extensions()
        print("已啟動")
        await bot.start(token)
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot 已手動關閉。")
    except Exception as e:
        print(f"Bot 啟動時發生錯誤: {e}")