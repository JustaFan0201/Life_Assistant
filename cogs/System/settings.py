# cogs/System/settings.py
import discord
from discord import app_commands
from discord.ext import commands

from database.db import DatabaseSession
from database.models import BotSettings
from .dashboard import deploy_dashboard_message

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _update_setting(self, interaction: discord.Interaction, column_name: str, value: int, success_msg: str):
        """
        根據當前伺服器 ID (Guild ID) 更新 BotSettings
        """
        guild_id = interaction.guild_id
        if not guild_id:
            return await interaction.response.send_message("❌ 請在伺服器內使用此指令。", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        try:
            with DatabaseSession() as db:
                settings = db.query(BotSettings).filter(BotSettings.id == guild_id).first()

                if not settings:
                    settings = BotSettings(id=guild_id)
                    db.add(settings)
                
                setattr(settings, column_name, value)
                db.commit()
                
            await interaction.followup.send(success_msg)
            print(f"⚙️ 設定更新 [Guild: {guild_id}]: {column_name} -> {value}")
            
        except Exception as e:
            print(f"❌ 資料庫錯誤: {e}")
            await interaction.followup.send(f"❌ 設定失敗：系統錯誤 ({e})")

    
    @app_commands.command(name="set_dashboard_channel", description="設定 Dashboard 主控台顯示的頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_dashboard_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            "dashboard_channel_id",
            channel.id, 
            f"✅ 已將 **Dashboard 頻道** 設定為：{channel.mention}"
        )
        await deploy_dashboard_message(self.bot, channel.id)

    @app_commands.command(name="set_login_notify_channel", description="設定登入通知發送的頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_login_notify_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            "login_notify_channel_id",
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
            "calendar_notify_channel_id", # 💡 對應 models.py 中的欄位名稱
            channel.id, 
            f"✅ 已將 **行程公開通知頻道** 設定為：{channel.mention}"
        )

    @app_commands.command(name="set_gpt_channel", description="設定GPT對話頻道")
    @app_commands.default_permissions(administrator=True)
    async def set_gpt_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self._update_setting(
            interaction, 
            "gpt_channel_id",
            channel.id, 
            f"✅ 已將 **GPT對話頻道** 設定為：{channel.mention}"
        )