import discord
from discord import ui

class DeleteItemBtn(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="刪除行程", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from ..View.ItineraryDeleteView import ItineraryDeleteView
        await interaction.response.edit_message(content="請選擇項目：", embed=None, view=ItineraryDeleteView(self.parent_view.cog, interaction.user.id))