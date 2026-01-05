import discord
from discord.ext import commands
from discord import app_commands

# 從 ui 資料夾引入 View
from .ui.menu_view import MainControlView
CHANNEL_ID = 1423551561187070022  # 請改成你要發送控制台的頻道 ID

class SystemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 負責產生 Embed 和 View，讓指令跟自動啟動都能共用
    def create_dashboard_ui(self):
        embed = discord.Embed(
            title="🎛️ Life Assistant 控制中心",
            description="請點擊下方按鈕來使用功能：",
            color=0x2b2d31
        )
        
        embed.add_field(name="🔮 今日運勢", value="AI 幫你算命，給予今日建議", inline=True)
        embed.add_field(name="💬 與 AI 對話", value="點擊按鈕直接向 GPT 提問", inline=True)
        
        embed.add_field(name="⚙️ 自動回覆", value="開啟/關閉頻道的自動監聽", inline=True)
        embed.add_field(name="ℹ️ 系統狀態", value="檢查機器人延遲與運作情形", inline=True)
        
        # 呼叫 View (按鈕都已經在 MainControlView 裡面裝好了)
        view = MainControlView(self.bot)
        return embed, view

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        
        if channel:
            try:
                await channel.purge(limit=10) 
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