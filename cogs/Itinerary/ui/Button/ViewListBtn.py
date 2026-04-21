import discord
from discord import ui

class ViewListBtn(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="查看行程表", style=discord.ButtonStyle.success, emoji="📋")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from ..View.ViewPageSelect import ViewPageSelect
        view = ViewPageSelect(self.parent_view.cog, interaction.user.id)
        await interaction.response.edit_message(embed=view.embed, view=view)