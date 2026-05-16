import discord
from cogs.BasicDiscordObject import LockableView
from cogs.Stock.ui.Select.StockDeleteSelect import StockDeleteSelect
from cogs.Stock.utils import StockManager
from cogs.Stock.ui.Button import StockBackToDashboardBtn
class StockDeleteView(LockableView):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        
        stocks = StockManager.get_user_stocks(user_id)

        if stocks:
            self.add_item(StockDeleteSelect(self.bot, stocks, self))
            
        self.add_item(StockBackToDashboardBtn(self.bot, row=1))

    @staticmethod
    def create_ui(bot, user_id):
        """
        靜態工廠方法：負責生成刪除介面的最新狀態
        """
        stocks = StockManager.get_user_stocks(user_id)
        
        if not stocks:
            desc = "您目前沒有監控任何股票，無法執行刪除操作！\n請點擊下方按鈕返回主畫面。"
        else:
            desc = "請從下方的下拉選單中，選擇您想要 **永久移除** 的股票。\n⚠️ 注意：移除後資料將無法復原。"

        embed = discord.Embed(
            title="🗑️ 移除股票監控",
            description=desc,
            color=discord.Color.red()
        )
        
        view = StockDeleteView(bot, user_id)
        return embed, view