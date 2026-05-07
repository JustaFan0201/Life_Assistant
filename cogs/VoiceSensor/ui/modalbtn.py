import discord

class ModalButton(discord.ui.Button):
    def __init__(self, label, modal_cls, bot):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.modal_cls = modal_cls
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.modal_cls(self.bot))