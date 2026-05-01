import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from cogs.System.ui.View.SystemStartView import MainControlView, SystemStartView
from cogs.System.utils import SystemManager

async def deploy_dashboard_message(bot, channel_id: int):
    """清除指定頻道的舊訊息，並發送 Dashboard 啟動介面"""
    try:
        channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
        
        if not channel:
            print(f"⚠️ [Dashboard] 找不到頻道 ID: {channel_id}")
            return
        try:
            await channel.purge(limit=15) 
        except Exception as e:
            print(f"⚠️ [Dashboard] 清除舊訊息失敗 (可能無權限): {e}")

        embed, view = SystemStartView.create_start_ui(bot)
        await channel.send(embed=embed, view=view)
        
        print(f"✅ [Dashboard] 入口介面已發送至頻道: {channel.name}")

    except Exception as e:
        print(f"❌ [Dashboard] 發送介面失敗: {e}")


class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="呼叫主控台")
    async def dashboard(self, interaction: discord.Interaction):
        await asyncio.to_thread(
            SystemManager.register_user, 
            interaction.user.id, 
            interaction.user.name
        )

        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        print(f"🚀 [System] 機器人已就緒，開始掃描各伺服器 Dashboard...")

        settings_list = await asyncio.to_thread(SystemManager.get_all_dashboard_settings)

        if not settings_list:
            print("⚠️ [Dashboard] 目前沒有任何伺服器設定 Dashboard 頻道。")
            return

        for settings in settings_list:
            guild_id = settings["guild_id"]
            channel_id = settings["channel_id"]
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                print(f"⏩ [Dashboard] 跳過伺服器 {guild_id} (機器人已不在該伺服器)")
                continue

            print(f"🔄 [Dashboard] 正在伺服器 '{guild.name}' ({guild_id}) 的頻道 {channel_id} 部署介面...")
            
            asyncio.create_task(deploy_dashboard_message(self.bot, channel_id))