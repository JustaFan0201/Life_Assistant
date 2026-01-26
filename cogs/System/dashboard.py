import discord
from discord.ext import commands
from discord import app_commands
import os

# 引入 MainControlView
from .ui.view import MainControlView

channel_id = os.getenv("Dashboard_Channel_ID")

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
    
        if not channel_id:
            print("❌ 錯誤：找不到 DASHBOARD_CHANNEL_ID 環境變數，請檢查 .env 檔案。")
            return
        try:
            channel = await self.bot.fetch_channel(int(channel_id))
            try:
                await channel.purge(limit=5) 
            except Exception as e:
                print(f"⚠️ 清除舊訊息失敗: {e}")

            embed, view = MainControlView.create_dashboard_ui(self.bot)
            
            await channel.send(embed=embed, view=view)
            print(f"✅ Dashboard 已發送至頻道: {channel.name} (ID: {channel.id})")

        except Exception as e:
            print(f"❌ Dashboard 發送失敗: {e}")

    @app_commands.command(name="dashboard", description="呼叫主控台")
    async def dashboard(self, interaction: discord.Interaction):
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view)