import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import traceback
from datetime import datetime, time

# 導入配置與自定義工具
from .stock_config import TW_TIME, MARKET_OPEN, MARKET_CLOSE, REPORT_TIME
from .utils.Stock_Manager import Stock_Manager
from .utils.fugle_api import get_stock_quote

class Stock(commands.Cog):
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager 
        self.api_token = os.getenv("FUGLE_TOKEN")
        self.api_lock = asyncio.Lock() # 確保背景監控與手動刷新不衝突
        
        # 啟動背景任務
        self.stock_monitor.start()
        self.market_report.start()

    def cog_unload(self):
        self.stock_monitor.cancel()
        self.market_report.cancel()

    # ==========================================
    #                指令入口 (UI)
    # ==========================================

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

    # ==========================================
    #              背景任務 (Tasks)
    # ==========================================

    @tasks.loop(minutes=1)
    async def stock_monitor(self):
        """每分鐘檢查一次股價 (免費版序列檢查模式)"""
        now = datetime.now(TW_TIME)
        if now.weekday() >= 5: return 
        current_time_val = now.hour * 100 + now.minute
        if not (MARKET_OPEN <= current_time_val <= MARKET_CLOSE): return

        try:
            with self.db_manager() as session:
                from database.models import UserStockWatch
                # 只檢查有設定預警的標的
                watches = session.query(UserStockWatch).filter(
                    (UserStockWatch.target_up.isnot(None)) | 
                    (UserStockWatch.target_down.isnot(None))
                ).all()
                
                for watch in watches:
                    async with self.api_lock:
                        info = get_stock_quote(watch.stock_symbol, self.api_token)
                    
                    if info and info.get('lastPrice'):
                        curr_price = info['lastPrice']
                        change_pct = info['changePercent'] / 100
                        
                        alert_msg = None
                        # 漲幅預警
                        if watch.target_up and change_pct >= watch.target_up:
                            alert_msg = f"🔺 **{info['name']} ({watch.stock_symbol})** 噴發！\n現價：`{curr_price}` (漲幅：`{change_pct*100:.2f}%`)"
                        # 跌幅預警
                        elif watch.target_down and change_pct <= watch.target_down:
                            alert_msg = f"🟢 **{info['name']} ({watch.stock_symbol})** 下跌！\n現價：`{curr_price}` (跌幅：`{change_pct*100:.2f}%`)"

                        # 發送通知並更新最後通知價格
                        if alert_msg and watch.last_notified_price != curr_price:
                            await self.send_dm(watch.user_id, alert_msg)
                            watch.last_notified_price = curr_price
                            session.commit()
                    
                    # 免費版限流：每支股票請求後強制暫停
                    await asyncio.sleep(1.1) 
                    
        except Exception as e:
            print(f"⚠️ 監控循環錯誤: {e}")

    @tasks.loop(time=REPORT_TIME)
    async def market_report(self):
        """收盤總結 (可視需求實作)"""
        pass

    # ==========================================
    #              內部輔助邏輯
    # ==========================================

    async def update_list_message(self, interaction: discord.Interaction, is_first=False):
        """
        詳細清單刷新邏輯：
        因應免費版限制，逐一獲取股價並漸進式更新 UI。
        """
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        try:
            from .ui.View.StockListView import StockListView
            from .ui.View.StockDashboardView import StockDashboardView

            # 1. 獲取資料庫資料
            stocks = Stock_Manager.get_user_stocks(self.db_manager, interaction.user.id)
            
            if not stocks:
                embed_msg, view_msg = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
                return await interaction.edit_original_response(
                    content="⚠️ 你的監控清單目前是空的。", 
                    embed=embed_msg, 
                    view=view_msg
                )

            # 2. 建立初始 Embed 提示更新中
            embed = discord.Embed(
                title=f"📊 {interaction.user.name} 的投資清單", 
                description="正在逐一抓取最新行情，請稍候...",
                color=discord.Color.blue(),
                timestamp=datetime.now(TW_TIME)
            )
            await interaction.edit_original_response(embed=embed)

            # 3. 序列抓取 (Sequential Fetch)
            for s in stocks:
                async with self.api_lock:
                    info = get_stock_quote(s.stock_symbol, self.api_token)
                
                if info and info.get('lastPrice'):
                    price = info['lastPrice']
                    pct = info['changePercent']
                    emoji = "🔺" if pct > 0 else "🟢" if pct < 0 else "⚪"
                    
                    # 計算損益
                    profit_data = Stock_Manager.calculate_profit(price, s.shares, s.total_cost)
                    
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
                
                # 每一支抓完就更新一次 Embed，讓使用者看到進度
                await interaction.edit_original_response(embed=embed)
                
                await asyncio.sleep(1.1)

            # 4. 完成後掛載 ListView
            view = StockListView(self.bot, interaction.user.id)
            await interaction.edit_original_response(content=None, embed=embed, view=view)

        except Exception as e:
            print(f"❌ update_list_message 發生錯誤: {e}")
            traceback.print_exc()
            try:
                await interaction.followup.send(f"❌ 更新失敗: {e}", ephemeral=True)
            except: pass

    async def send_dm(self, user_id, content):
        """發送私訊輔助函數"""
        try:
            user = await self.bot.fetch_user(user_id)
            if user: await user.send(content)
        except Exception as e:
            print(f"❌ 無法發送私訊給 {user_id}: {e}")


async def setup(bot):
    db_manager = getattr(bot, "db_session", None)
    await bot.add_cog(Stock(bot, db_manager))