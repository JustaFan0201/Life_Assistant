import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Stock.ui.View.StockListView import StockListView

class StockRefreshBtn(SafeButton):
    def __init__(self, bot, row=0):
        super().__init__(
            label="刷新現價損益", 
            style=discord.ButtonStyle.success, 
            emoji="🔄", 
            row=row
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        await StockListView.load_and_render_ui(interaction, self.bot)