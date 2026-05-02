import discord
from discord import ui

class BackToGmailDashboardBtn(ui.Button):
    def __init__(self, bot, gmail_cog, user_id, row=1):
        super().__init__(label="返回管理中心", style=discord.ButtonStyle.danger, row=row)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        embed, view = GmailDashboardView.create_ui(self.bot, self.gmail_cog, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)