import discord
from discord import ui

class NextStepBtn(ui.Button):
    def __init__(self, time_data):
        self.time_data = time_data
        super().__init__(label="下一步：填寫細節", style=discord.ButtonStyle.primary, row=4)
        
    async def callback(self, interaction: discord.Interaction):
        from ..Modal.ItineraryModal import ItineraryModal
        await interaction.response.send_modal(ItineraryModal(self.time_data))