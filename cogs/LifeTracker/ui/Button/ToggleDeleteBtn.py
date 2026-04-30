import discord
from discord import ui

class ToggleDeleteBtn(ui.Button):
    def __init__(self, bot, category_id, subcats_info,label="刪除標籤", emoji="🗑️", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id
        self.subcats_info = subcats_info

    async def callback(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
        embed, view =await ManageSubcatView.create_ui(self.bot, self.category_id, mode="delete")
        await interaction.response.edit_message(embed=embed, view=view)