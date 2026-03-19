import discord
from discord import ui

class ManageSubcatBtn(ui.Button):
    def __init__(self, bot, category_id):
        super().__init__(label="管理子分類", style=discord.ButtonStyle.primary, emoji="⚙️", row=0)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        # 點擊後，切換到我們等一下要寫的「管理面板」
        from cogs.LifeTracker.ui.View import ManageSubcatView
        embed, view = ManageSubcatView.create_ui(self.bot, self.category_id)
        await interaction.response.edit_message(embed=embed, view=view)