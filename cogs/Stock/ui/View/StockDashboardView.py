import discord
from cogs.BasicDiscordObject import LockableView
from cogs.System.ui.Button import BackToMainButton
from cogs.Stock.utils import Stock_Manager

class StockDashboardView(LockableView):
    def __init__(self, bot, user_id):
        """
        初始化儀表板 View，將各個按鈕零件裝上去
        """
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        
        from cogs.Stock.ui.Button import StockAddBtn, StockDeleteBtn, StockListBtn, StockQueryBtn
        
        self.add_item(StockListBtn(self.bot))   # 詳細損益清單
        self.add_item(StockAddBtn(self.bot))    # 新增監控
        self.add_item(StockDeleteBtn(self.bot)) # 移除監控
        self.add_item(StockQueryBtn(self.bot))
        
        if BackToMainButton:
            self.add_item(BackToMainButton(self.bot, row=1))

    @staticmethod
    def create_dashboard(bot, user_id: int):
        """
        靜態工廠方法：負責從資料庫抓取數據並生成 Embed 與 View
        """

        stocks = Stock_Manager.get_user_stocks(user_id)
        
        embed = discord.Embed(
            title="📈 股票監控中心",
            description="歡迎回來！以下是你目前的監控標的概覽。\n點擊 **詳細損益清單** 可查看最新的即時現價與投資報酬率。",
            color=discord.Color.dark_green(),
            timestamp=discord.utils.utcnow()
        )
        
        if stocks:
            stock_tags = " ".join([f"`{s.stock_symbol}`" for s in stocks])
            stock_list_text = "\n".join([f"• **{s.stock_name}** ({s.stock_symbol})" for s in stocks])
            
            embed.add_field(name="🏷️ 監控代碼", value=stock_tags, inline=False)
            embed.add_field(name="📂 清單明細", value=stock_list_text, inline=False)
            embed.set_footer(text="數據更新：Fugle API | 顯示之損益已預扣稅費")
        else:
            embed.add_field(
                name="📂 監控清單", 
                value="目前還沒有監控中的標的喔！\n請點擊下方的 **新增監控** 按鈕開始你的第一筆紀錄。", 
                inline=False
            )
            embed.set_footer(text="提示：你可以輸入持有股數與總成本來計算精確損益。")

        view = StockDashboardView(bot, user_id)
        return embed, view