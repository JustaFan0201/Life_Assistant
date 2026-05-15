import discord
from discord import ui

class HelpBtn(ui.Button):
    def __init__(self, user_id, row=1):
        super().__init__(label="使用教學", style=discord.ButtonStyle.secondary, emoji="📖", row=row)
        self.user_id = user_id


    async def callback(self, interaction: discord.Interaction):
        from cogs.Gmail.ui.View.HelpView import HelpView
        
        view = HelpView(self.user_id)
        await interaction.response.edit_message(embed=view.generate_embed(), view=view)