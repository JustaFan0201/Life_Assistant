import discord
from discord import ui
from ..Modal.ContactModals import EditEmailModal

class EditContactBtn(ui.Button):
    def __init__(self, cog, user_id, nickname):
        super().__init__(label="修改 Email", style=discord.ButtonStyle.primary, emoji="✏️")
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EditEmailModal(self.cog, self.user_id, self.nickname))