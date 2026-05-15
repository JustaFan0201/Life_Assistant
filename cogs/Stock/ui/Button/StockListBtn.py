import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Stock.stock_cog import update_list_message

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
        await update_list_message(self.bot, interaction, is_first=False)