import discord
from discord import ui

class NextPageBtn(ui.Button):
    def __init__(self, parent_view):
        super().__init__(label="下一頁 ❯", row=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        from ..View.ViewPageSelect import ViewPageSelect
        view = ViewPageSelect(self.parent_view.cog, self.parent_view.user_id, self.parent_view.page + 1)
        await interaction.response.edit_message(embed=view.embed, view=view)