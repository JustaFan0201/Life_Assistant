import discord
from discord import ui
#狀態按鈕，顯示系統延遲
class StatusButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="系統狀態", style=discord.ButtonStyle.gray, row=1, emoji="ℹ️")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"✅ 系統運作中，延遲：{latency}ms", ephemeral=True)
# 返回主選單按鈕
class BackToMainButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="返回主選單",
            style=discord.ButtonStyle.secondary,
            row=4
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        system_cog = self.bot.get_cog("SystemCog")

        if system_cog:
            embed, view = system_cog.create_dashboard_ui()
            
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ 錯誤：找不到系統核心模組。", ephemeral=True)
# 前往 GPT UI按鈕
class GoToGPTButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="AI 助手功能", 
            style=discord.ButtonStyle.primary, 
            emoji="🤖",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from ...GPT.ui.view import GPTDashboardView
        
        embed = discord.Embed(
            title="🤖 AI 助手控制台",
            description="這裡集合了所有 GPT 相關功能，請選擇：",
            color=0x1abc9c
        )
        embed.add_field(name="功能列表", value="🔮 運勢\n💬 對話\n⚙️ 設定", inline=False)
        
        view = GPTDashboardView(self.bot)
        
        await interaction.response.edit_message(embed=embed, view=view)

class GoToTHSRButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="高鐵時刻表", 
            style=discord.ButtonStyle.success, 
            emoji="🚄",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 1. 獲取 Ticket Cog
        ticket_cog = self.bot.get_cog("THSR_CheckTimeStampCog")
        
        if ticket_cog:
            # 2. 呼叫 Cog 裡面的 UI 產生器
            embed, view = ticket_cog.create_ticket_dashboard_ui()
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ 錯誤：找不到高鐵模組。", ephemeral=True)