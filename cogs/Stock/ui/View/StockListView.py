import discord
from cogs.BasicDiscordObject import LockableView
from ..Button.StockRefreshBtn import StockRefreshBtn
from ..Button.StockBackToDashboardBtn import StockBackToDashboardBtn

class StockListView(LockableView):
    def __init__(self, bot, user_id):
        super().__init__(timeout=180) # 清單可以設長一點的 timeout
        self.bot = bot
        self.user_id = user_id
        
        # 加入刷新按鈕 (會觸發 Cog 的 update_list_message)
        self.add_item(StockRefreshBtn(self.bot))
        
        # 加入返回股票主分頁按鈕
        self.add_item(StockBackToDashboardBtn(self.bot))