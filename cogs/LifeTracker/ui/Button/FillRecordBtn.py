import discord
from discord import ui

class FillRecordBtn(ui.Button):
    def __init__(self, parent_view, label="", emoji="✏️", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.Modal import InputValueModal
        await interaction.response.send_modal(InputValueModal(self.parent_view, self.parent_view.cat_info['fields']))