import discord
from discord import app_commands
from discord.ext import commands

# 定義名為 Main 的 Cog
class HelloBack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 關鍵字觸發
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print(f"{__name__} loaded successfully")
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        if message.content == "Hello":
            await message.channel.send("Hello, world!")

    # 前綴指令
    @app_commands.command(name="hello",description="send helloback to you.")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello, world!")

# Cog 載入 Bot 中
async def setup(bot):
    await bot.add_cog(HelloBack(bot))