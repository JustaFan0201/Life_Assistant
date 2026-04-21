import discord
from discord import ui
from ..View.ContactViews import RecipientSelectView

class SendMailBtn(ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="撰寫郵件", style=discord.ButtonStyle.primary, emoji="✍️")
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        view = RecipientSelectView(self.cog, self.user_id)
        await interaction.response.send_message("請選擇收件人：", view=view, ephemeral=True)