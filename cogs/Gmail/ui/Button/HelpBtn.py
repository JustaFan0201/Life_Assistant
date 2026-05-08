import discord
from discord import ui

class HelpBtn(ui.Button):
    def __init__(self, bot, gmail_cog, user_id, row=1):
        super().__init__(label="使用教學", style=discord.ButtonStyle.secondary, emoji="📖", row=row)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.Gmail.ui.View.HelpView import HelpView
        
        view = HelpView(self.bot, self.gmail_cog, self.user_id)
        await interaction.response.edit_message(embed=view.generate_embed(), view=view)