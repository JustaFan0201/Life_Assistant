import discord
from cogs.BasicDiscordObject import LockableView
from cogs.Stock.ui.Button import StockRefreshBtn,StockBackToDashboardBtn

class StockListView(LockableView):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        
        self.add_item(StockRefreshBtn(self.bot, row=0))
        self.add_item(StockBackToDashboardBtn(self.bot, row=0))