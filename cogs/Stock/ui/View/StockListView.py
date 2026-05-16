import discord
import asyncio
import traceback
from datetime import datetime
from cogs.BasicDiscordObject import LockableView
from cogs.Stock.utils import StockManager, get_stock_quote, fugle_api_lock
from cogs.Stock.stock_config import FUGLE_TOKEN, TW_TZ

class StockListView(LockableView):
    def __init__(self, bot, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        
        from cogs.Stock.ui.Button.StockRefreshBtn import StockRefreshBtn
        from cogs.Stock.ui.Button.StockBackToDashboardBtn import StockBackToDashboardBtn
        
        self.add_item(StockRefreshBtn(self.bot, row=0))
        self.add_item(StockBackToDashboardBtn(self.bot, row=0))

    @staticmethod
    async def create_ui(bot, user_id: int, user_name: str):
        try:
            stocks = StockManager.get_user_stocks(user_id)

            if not stocks:
                from cogs.Stock.ui.View.StockDashboardView import StockDashboardView
                return StockDashboardView.create_dashboard(bot, user_id)

            embed = discord.Embed(
                title=f"📊 {user_name} 的投資清單", 
                color=discord.Color.blue(),
                timestamp=datetime.now(TW_TZ)
            )

            for s in stocks:
                async with fugle_api_lock:
                    info = get_stock_quote(s.stock_symbol, FUGLE_TOKEN)
                
                if info and info.get('lastPrice'):
                    price = info['lastPrice']
                    pct = info['changePercent']
                    emoji = "🔺" if pct > 0 else "🟢" if pct < 0 else "⚪"
                    
                    profit_data = StockManager.calculate_profit(price, s.shares, s.total_cost)
                    
                    if profit_data:
                        roi_str = (
                            f"\n均價: `{profit_data['avg_price']:.2f}` | 持股: `{s.shares}`"
                            f"\n預估盈虧: `NT$ {profit_data['net_profit']:,}`"
                            f"\n實質投報: `{profit_data['roi']:.2f}%`"
                        )
                    else:
                        roi_str = f"\n成本: `{s.buy_price or 'N/A'}`"

                    embed.add_field(
                        name=f"{info['name']} ({s.stock_symbol})", 
                        value=f"現價: `{price}` ({emoji}{pct:.2f}%){roi_str}", 
                        inline=False
                    )
                else:
                    embed.add_field(
                        name=f"⚠️ 讀取失敗 ({s.stock_symbol})", 
                        value="無法取得最新股價 (可能為 API 限流、網路異常或下市)", 
                        inline=False
                    )
                
                await asyncio.sleep(1.1)

            view = StockListView(bot, user_id)
            return embed, view

        except Exception as e:
            print(f"❌ StockListView.create_ui 發生錯誤: {e}")
            traceback.print_exc()
            return None, None