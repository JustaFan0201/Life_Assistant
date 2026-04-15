import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from .ui.view import MainControlView, SystemStartView

from database.db import SessionLocal
from database.models import User, BotSettings

async def deploy_dashboard_message(bot, channel_id: int):
    """清除指定頻道的舊訊息，並發送 Dashboard 啟動介面"""
    try:
        channel = bot.get_channel(int(channel_id)) or await bot.fetch_channel(int(channel_id))
        
        if not channel:
            print(f"⚠️ [Dashboard] 找不到頻道 ID: {channel_id}")
            return
        try:
            await channel.purge(
                limit=10,
                check=lambda m: m.author == bot.user
            ) 
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

    def _register_user(self, discord_id: int, username: str):
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.discord_id == discord_id).first()
                
                if not user:
                    new_user = User(
                        discord_id=discord_id,
                        username=username,
                    )
                    db.add(new_user)
                    db.commit()
                    print(f"🆕 [Database] 新使用者註冊: {username} ({discord_id})")
                else:
                    if user.username != username:
                        user.username = username
                        db.commit()
                        # print(f"🔄 [Database] 更新使用者名稱: {username}")
                        
        except Exception as e:
            print(f"❌ [Database] 使用者註冊失敗: {e}")


    @app_commands.command(name="dashboard", description="呼叫主控台")
    async def dashboard(self, interaction: discord.Interaction):
        await asyncio.to_thread(
            self._register_user, 
            interaction.user.id, 
            interaction.user.name
        )

        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        
        channel_id = None
        try:
            with SessionLocal() as db:
                settings = db.query(BotSettings).filter(BotSettings.id == 1).first()
                if settings and settings.dashboard_channel_id:
                    channel_id = settings.dashboard_channel_id
                    print(f"🔍 [Dashboard] 從資料庫讀取到 Channel ID: {channel_id}")
                else:
                    print("⚠️ [Dashboard] 資料庫中尚未設定 Dashboard 頻道。")
        except Exception as e:
            print(f"❌ [Dashboard] 讀取資料庫失敗: {e}")
            return

        if not channel_id:
            print("👉 請使用 `/set_dashboard_channel` 指令來設定顯示頻道。")
            return

        await deploy_dashboard_message(self.bot, channel_id)
