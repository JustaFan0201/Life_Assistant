import discord
from cogs.LifeTracker.ui.Modal.EInvoiceSetupModal import EInvoiceSetupModal

class SetupEInvoiceBtn(discord.ui.Button):
    def __init__(self, bot, category_id: int):
        super().__init__(style=discord.ButtonStyle.primary, label="⚙️ 設定個資")
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EInvoiceSetupModal(self.bot, self.category_id))