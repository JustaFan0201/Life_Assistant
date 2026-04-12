import discord
from cogs.BasicDiscordObject import SafeButton

class BackToLifeDashboardBtn(SafeButton):
    def __init__(self, bot, label="", emoji="🔙", row=4):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        
    async def do_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.LifeDashboardView import LifeDashboardView

        embed, view = LifeDashboardView.create_dashboard(self.bot, interaction.user.id)
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])