import discord
from discord import ui

class AddItemBtn(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="新增行程", style=discord.ButtonStyle.primary, emoji="➕")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from ..View.ItineraryAddView import ItineraryAddView
        embed = discord.Embed(title="➕ 新增行程", color=0x3498db)
        await interaction.response.edit_message(embed=embed, view=ItineraryAddView(self.parent_view.cog))