import discord
from discord import ui
from cogs.LifeTracker.ui.Modal.SetupCategoryModal import SetupCategoryModal

class SetupBtn(ui.Button):
    def __init__(self, bot, label="", emoji="➕", row=1):
        super().__init__(
            label=label, 
            emoji=emoji,
            style=discord.ButtonStyle.green, 
            custom_id="life_setup_btn", # 注意：如果是 Persistent View，ID 必須唯一
            row=row
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SetupCategoryModal(self.bot))
