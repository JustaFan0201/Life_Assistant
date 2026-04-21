import discord
from discord import ui
from ..Modal.SendMailModal import EmailSendModal

class ManualInputBtn(ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="直接手動輸入", style=discord.ButtonStyle.secondary)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmailSendModal(self.cog, self.user_id))