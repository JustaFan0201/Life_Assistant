import discord
from discord.ext import commands
from discord import app_commands

from .ui.view import MainControlView

from database.db import DatabaseSession
from database.models import BotSettings

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="呼叫主控台")
    async def dashboard(self, interaction: discord.Interaction):
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


    '''@commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        
        channel_id = None
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

        # --- 步驟 2: 檢查 ID 是否存在 ---
        if not channel_id:
            print("👉 請使用 `/set_dashboard_channel` 指令來設定顯示頻道。")
            return

        # --- 步驟 3: 發送介面 ---
        try:
            # 使用 fetch_channel 確保能抓到頻道物件
            channel = await self.bot.fetch_channel(int(channel_id))
            
            # 清除舊訊息 (保持頻道乾淨)
            try:
                await channel.purge(limit=5) 
            except Exception as e:
                print(f"⚠️ [Dashboard] 清除舊訊息失敗 (可能是權限不足或訊息太舊): {e}")

            # 建立並發送 Dashboard
            embed, view = MainControlView.create_dashboard_ui(self.bot)
            await channel.send(embed=embed, view=view)
            
            print(f"✅ [Dashboard] 已成功發送至頻道: {channel.name} (ID: {channel.id})")

        except discord.NotFound:
            print(f"❌ [Dashboard] 錯誤：找不到頻道 ID {channel_id} (可能已被刪除或 Bot 不在該伺服器)")
        except discord.Forbidden:
            print(f"❌ [Dashboard] 錯誤：Bot 沒有權限在該頻道發言")
        except Exception as e:
            print(f"❌ [Dashboard] 發送失敗: {e}")'''
