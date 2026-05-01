import discord
from discord import ui

class BackToMainButton(ui.Button):
    def __init__(self, bot, label="返回主選單", emoji=None, row=4):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.danger,
            row=row
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.System.ui.View import MainControlView 
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])