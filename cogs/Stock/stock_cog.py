import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import traceback
from datetime import datetime

# 導入配置與自定義工具
from cogs.Stock.stock_config import MARKET_OPEN, MARKET_CLOSE, REPORT_TIME, FUGLE_TOKEN, TW_TZ
from cogs.Stock.utils import StockManager, get_stock_quote,fugle_api_lock

class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # 啟動背景任務
        self.stock_monitor.start()
        self.market_report.start()

    def cog_unload(self):
        self.stock_monitor.cancel()
        self.market_report.cancel()

    # 指令入口 (UI)
    @app_commands.command(name="stock", description="開啟股票監控儀表板")
    async def stock_dashboard(self, interaction: discord.Interaction):
        """進入股票模組的主入口"""
        try:
            from .ui.View.StockDashboardView import StockDashboardView
            # 產生 Embed 與 View
            embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"❌ 開啟儀表板失敗: {e}")
            traceback.print_exc()

    # 背景任務 (Tasks)
    @tasks.loop(minutes=1)
    async def stock_monitor(self):
        """每分鐘檢查一次股價 (免費版序列檢查模式)"""
        now = datetime.now(TW_TZ)
        if now.weekday() >= 5: return 
        current_time_val = now.hour * 100 + now.minute
        if not (MARKET_OPEN <= current_time_val <= MARKET_CLOSE): return

        try:
            # 🌟 [修改] 改用 Manager API 獲取資料
            watches = StockManager.get_alert_watches()
            
            for watch in watches:
                async with fugle_api_lock:
                    info = get_stock_quote(watch['stock_symbol'], FUGLE_TOKEN)
                
                if info and info.get('lastPrice'):
                    curr_price = info['lastPrice']
                    change_pct = info['changePercent'] / 100
                    
                    alert_msg = None
                    # 漲幅預警
                    if watch['target_up'] and change_pct >= watch['target_up']:
                        alert_msg = f"🔺 **{info['name']} ({watch['stock_symbol']})** 噴發！\n現價：`{curr_price}` (漲幅：`{change_pct*100:.2f}%`)"
                    # 跌幅預警
                    elif watch['target_down'] and change_pct <= watch['target_down']:
                        alert_msg = f"🟢 **{info['name']} ({watch['stock_symbol']})** 下跌！\n現價：`{curr_price}` (跌幅：`{change_pct*100:.2f}%`)"

                    # 發送通知並更新最後通知價格
                    if alert_msg and watch['last_notified_price'] != curr_price:
                        await self.send_dm(watch['user_id'], alert_msg)
                        
                        # 🌟 [修改] 改用 Manager API 執行更新操作
                        StockManager.update_notified_price(watch['user_id'], watch['stock_symbol'], curr_price)
                
                # 免費版限流：每支股票請求後強制暫停
                await asyncio.sleep(1.1) 
                
        except Exception as e:
            print(f"⚠️ 監控循環錯誤: {e}")

    @tasks.loop(time=REPORT_TIME)
    async def market_report(self):
        """收盤總結 (可視需求實作)"""
        pass

    async def send_dm(self, user_id, content):
        """發送私訊輔助函數"""
        try:
            user = await self.bot.fetch_user(user_id)
            if user: await user.send(content)
        except Exception as e:
            print(f"❌ 無法發送私訊給 {user_id}: {e}")
