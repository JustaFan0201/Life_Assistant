import discord
from cogs.BasicDiscordObject import LockableView
from cogs.Stock.ui.Select.StockDeleteSelect import StockDeleteSelect

class StockDeleteView(LockableView):
    def __init__(self, cog, user_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.bot = cog.bot
        
        from cogs.Stock.utils.Stock_Manager import Stock_Manager
        stocks = Stock_Manager.get_user_stocks(self.cog.db_manager, user_id)

        # 1. 放入下拉選單 (Row 0)
        if stocks:
            self.add_item(StockDeleteSelect(self.bot, stocks, self))
            
        # 2. 放入返回儀表板按鈕 (Row 1，避免跟選單擠在一起)
        try:
            from cogs.Stock.ui.Button.StockBackToDashboardBtn import StockBackToDashboardBtn
            self.add_item(StockBackToDashboardBtn(self.bot, row=1))
        except ImportError:
            pass

    @staticmethod
    def create_ui(cog, user_id):
        from cogs.Stock.utils.Stock_Manager import Stock_Manager
        stocks = Stock_Manager.get_user_stocks(cog.db_manager, user_id)
        
        if not stocks:
            desc = "您目前沒有監控任何股票，無法執行刪除操作！\n請點擊下方按鈕返回主畫面。"
        else:
            desc = "請從下方的下拉選單中，選擇您想要 **永久移除** 的股票。\n⚠️ 注意：移除後資料將無法復原。"

        embed = discord.Embed(
            title="🗑️ 移除股票監控",
            description=desc,
            color=discord.Color.red()
        )
        
        view = StockDeleteView(cog, user_id)
        return embed, view