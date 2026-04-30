# cogs/LifeTracker/ui/Button/ToggleRangeEditBtn.py (原本的 CustomRangeBtn 位置)
import discord
from cogs.BasicDiscordObject import SafeButton

class ToggleRangeEditBtn(SafeButton):
    def __init__(self, bot, category_id, row=2):
        super().__init__(label="管理區間", emoji="⚙️", style=discord.ButtonStyle.secondary, row=row)
        self.bot = bot
        self.category_id = category_id

    async def do_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.RangeEditView import RangeEditView
        embed, view = await RangeEditView.create_ui(self.bot, self.category_id)
        await interaction.edit_original_response(embed=embed, view=view, attachments=[])