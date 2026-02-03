import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from .ui.view import MainControlView, SystemStartView

from database.db import DatabaseSession
from database.models import User, BotSettings

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _register_user(self, discord_id: int, username: str):
        try:
            with DatabaseSession() as db:
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
        # (讀取資料庫 channel_id 的邏輯保持不變)
        try:
            with DatabaseSession() as db:
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

        try:
            channel = await self.bot.fetch_channel(int(channel_id))
            
            # 清除舊訊息
            try:
                await channel.purge(limit=5) 
            except Exception as e:
                print(f"⚠️ [Dashboard] 清除舊訊息失敗: {e}")

            # ★★★ 關鍵修改：發送「啟動介面 (SystemStartView)」 ★★★
            # 這樣公共頻道就只會看到一個「開啟全能助手」的按鈕
            embed, view = SystemStartView.create_start_ui(self.bot)
            await channel.send(embed=embed, view=view)
            
            print(f"✅ [Dashboard] 入口介面已發送至頻道: {channel.name}")

        except Exception as e:
            print(f"❌ [Dashboard] 發送失敗: {e}")
