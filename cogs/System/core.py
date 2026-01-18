import discord
from discord.ext import commands
from discord import app_commands

from .ui.menu_view import MainControlView
CHANNEL_ID = 1423551561187070022
# 系統模組的 Cog 主要用來顯示文字訊息 可以依照以下格式 新增介紹功能文字
class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    def create_dashboard_ui(self):
        embed = discord.Embed(
            title="Life Assistant 控制中心",
            description="> 歡迎使用全能助手，請點擊下方按鈕操作：",
            color=0x2b2d31,
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png")

        embed.add_field(
            name="🤖 AI 助手", 
            value="包含：今日運勢、GPT 對話", 
            inline=False
        )

        embed.add_field(
            name="🚄 生活工具", 
            value="包含：高鐵時刻表查詢",
            inline=True
        )

        embed.add_field(
            name="ℹ️ 系統狀態", 
            value="檢查機器人延遲 (Ping)", 
            inline=False
        )

        embed.set_footer(
            text="Life Assistant v0.1", 
            icon_url="https://cdn-icons-png.flaticon.com/512/906/906324.png" # 資訊小圖標
        )

        view = MainControlView(self.bot)
        return embed, view

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        
        if channel:
            try:
                await channel.purge(limit=5) 
            except Exception as e:
                print(f"清除舊訊息失敗 (可能是權限不足): {e}")

            embed, view = self.create_dashboard_ui()
            await channel.send(embed=embed, view=view)
            print(f"✅ Dashboard 已發送至頻道: {channel.name}")
        else:
            print(f"❌ 找不到頻道 ID: {CHANNEL_ID}，請確認機器人是否有權限看到該頻道。")


    @app_commands.command(name="dashboard", description="呼叫主控台")
    async def dashboard(self, interaction: discord.Interaction):
        embed, view = self.create_dashboard_ui()
        await interaction.response.send_message(embed=embed, view=view)