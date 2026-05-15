import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Stock.stock_cog import update_list_message

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
        """
        按下按鈕後執行的動作
        """
        await update_list_message(self.bot, interaction, is_first=False)