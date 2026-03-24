import discord
from discord import ui

class BackToLifeDashboardBtn(ui.Button):
    def __init__(self, bot, label="", emoji="🔙", row=4):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        
    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import LifeDashboardView
        embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])