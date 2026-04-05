import discord
from discord import ui
class CustomRangeBtn(ui.Button):
    def __init__(self, bot, category_id, row=1):
        super().__init__(
            label="",
            emoji="⚙️",
            style=discord.ButtonStyle.secondary,
            row=row
        )
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal.SetRangeModal import SetRangeModal
        await interaction.response.send_modal(SetRangeModal(self.bot, self.category_id))