import discord
from discord import ui

class NextStepBtn(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="下一步：填寫細節", style=discord.ButtonStyle.primary, row=4)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from ..Modal.ItineraryModal import ItineraryModal
        await interaction.response.send_modal(ItineraryModal(self.parent_view.new_data, self.parent_view.cog))