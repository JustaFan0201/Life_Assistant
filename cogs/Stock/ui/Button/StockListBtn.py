import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Stock.ui.View.StockListView import StockListView

class StockListBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(
            label="詳細損益清單", 
            style=discord.ButtonStyle.success, 
            emoji="📋", 
            row=0
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        await StockListView.load_and_render_ui(interaction, self.bot)