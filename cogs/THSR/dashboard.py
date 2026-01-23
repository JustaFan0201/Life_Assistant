import discord
from discord.ext import commands
from discord import app_commands

# 引入 Dashboard View
from .ui.view import THSR_DashboardView

class THSR_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[THSR] CheckTimeStamp Module loaded.")

    '''@app_commands.command(name="thsr", description="開啟高鐵服務中心")
    async def thsr(self, interaction: discord.Interaction):
        embed, view = TicketDashboardView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view)'''

async def setup(bot):
    await bot.add_cog(THSR_Cog(bot))