import discord
from discord import ui

class GoToLifeTrackerButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="生活日記", 
            style=discord.ButtonStyle.primary, 
            emoji="📔",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        try:
            from cogs.LifeTracker.ui.View import LifeDashboardView
            
            embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"❌ 跳轉失敗，原因：{e}", ephemeral=True)