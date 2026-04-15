# cogs/System/settings.py
import discord
from discord import app_commands
from discord.ext import commands

from database.models import BotSettings
from .dashboard import deploy_dashboard_message
from database.db_utils import set_botsettings

    
class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _update_setting(self, interaction: discord.Interaction, column, value: int, success_msg: str):
        """
        更新 BotSettings 表中 ID=1 的特定欄位
        """
        
        print("開始更新BotSettings")
        await interaction.response.defer(ephemeral=True)
        if set_botsettings(column, value):
            await interaction.followup.send(success_msg)
            print(f"⚙️ (User: {interaction.user})")
        else:
            await interaction.followup.send("❌ 設定失敗：系統錯誤")

    
    @app_commands.command(name="set_dashboard_channel", description="設定 Dashboard 主控台顯示的頻道")
    @app_commands.default_permissions(administrator=True) # 只有管理員能用
    async def set_dashboard_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            BotSettings.dashboard_channel_id,
            channel.id, 
            f"✅ 已將 **Dashboard 頻道** 設定為：{channel.mention}"
        )
        await deploy_dashboard_message(self.bot, channel.id)

    @app_commands.command(name="set_login_notify_channel", description="設定登入通知發送的頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_login_notify_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            BotSettings.login_notify_channel_id,
            channel.id, 
            f"✅ 已將 **登入通知頻道** 設定為：{channel.mention}"
        )

    @app_commands.command(name="set_calendar_channel", description="設定行程公開提醒的通知頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_calendar_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """
        設定行程模組在「公開提醒」時要發送的頻道
        """
        await self._update_setting(
            interaction, 
            BotSettings.calendar_notify_channel_id,
            channel.id, 
            f"✅ 已將 **行程公開通知頻道** 設定為：{channel.mention}"
        )

    @app_commands.command(name="set_gpt_channel", description="設定GPT對話頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_gpt_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            BotSettings.gpt_channel_id,
            channel.id, 
            f"✅ 已將 **GPT對話頻道** 設定為：{channel.mention}"
        )