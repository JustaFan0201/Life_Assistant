import discord
from cogs.Base import SafeButton

class ManageSubcatBtn(SafeButton):
    def __init__(self, bot, category_id, label="", emoji="🏷️", row=0):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id

    async def do_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.ManageSubcatView import ManageSubcatView
        embed, view = await ManageSubcatView.create_ui(self.bot, self.category_id)
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])