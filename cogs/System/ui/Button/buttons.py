import discord
from discord import ui
        
'''# 前往 GPT UI按鈕
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
        
        await interaction.response.edit_message(embed=embed, view=view)'''

'''class GoToTHSRButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="高鐵功能服務", 
            style=discord.ButtonStyle.primary, 
            emoji="🚄",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.THSR.ui.view import THSR_DashboardView
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)'''
