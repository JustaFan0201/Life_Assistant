import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
from datetime import datetime, timedelta, timezone, time
from .utils.fugle_api import get_stock_snapshot
from database.models import UserStockWatch, User
from .stock_ui import StockAddModal, StockRemoveSelect, StockListView, ui

# 定義台灣時區 (UTC+8)
TW_TIME = timezone(timedelta(hours=8))
REPORT_TIME = time(hour=13, minute=45, tzinfo=TW_TIME)


class Stock(commands.Cog):
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager 
        self.api_token = os.getenv("FUGLE_TOKEN")
        self.api_lock = asyncio.Lock()
        
        # 啟動背景任務
        self.stock_monitor.start()
        self.market_report.start()

    def cog_unload(self):
        self.stock_monitor.cancel()
        self.market_report.cancel()

    # --- 背景監控任務 ---
    @tasks.loop(minutes=1)
    async def stock_monitor(self):
        now = datetime.now(TW_TIME)
        if now.weekday() >= 5: return 
        current_time_val = now.hour * 100 + now.minute
        if not (900 <= current_time_val <= 1335): return

        with self.db_manager() as session:
            watches = session.query(UserStockWatch).all()
            for watch in watches:
                if watch.target_up is None and watch.target_down is None: continue

                async with self.api_lock:
                    try:
                        info = get_stock_snapshot(watch.stock_symbol, self.api_token)
                        if info and info['price'] is not None:
                            curr_price = info['price']
                            change_pct = info['change_pct']
                            real_change = change_pct / 100 if abs(change_pct) > 1 else change_pct
                            
                            msg = None
                            if watch.target_up is not None and real_change >= watch.target_up:
                                msg = f"🔺 **{info['name']} ({watch.stock_symbol})** 噴發！\n現價：`{curr_price}` (漲：`{real_change*100:.2f}%`)"
                            elif watch.target_down is not None and real_change <= watch.target_down:
                                msg = f"🟢 **{info['name']} ({watch.stock_symbol})** 下跌！\n現價：`{curr_price}` (跌：`{real_change*100:.2f}%`)"

                            if msg and watch.last_notified_price != curr_price:
                                await self.send_dm(watch.user_id, msg)
                                watch.last_notified_price = curr_price
                                session.commit()
                    except Exception as e:
                        print(f"監控錯誤: {e}")
                await asyncio.sleep(1)

    # --- 收盤戰報任務 ---
    @tasks.loop(time=REPORT_TIME)
    async def market_report(self):
        # ... (保留上一版本的戰報邏輯) ...
        pass

    # --- UI 指令集 ---

    @app_commands.command(name="stock_add", description="彈窗式新增股票監控")
    async def stock_add(self, interaction: discord.Interaction):
        # 💡 注意：Modal 必須直接回覆，不能先 defer
        try:
            await interaction.response.send_modal(
                StockAddModal(self.db_manager, self.api_token, self.api_lock)
            )
        except Exception as e:
            print(f"❌ 無法發送 Modal: {e}")

    @app_commands.command(name="stock_list", description="查看我的股票清單 (帶重新整理按鈕)")
    async def stock_list(self, interaction: discord.Interaction):
        await self.update_list_message(interaction, is_first=True)

    @app_commands.command(name="stock_remove", description="下拉選單刪除股票")
    async def stock_remove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        with self.db_manager() as session:
            user = session.query(User).filter_by(discord_id=interaction.user.id).first()
            if not user or not user.stocks:
                return await interaction.followup.send("⚠️ 你的清單目前是空的。")
            
            view = ui.View()
            view.add_item(StockRemoveSelect(user.stocks, self.db_manager))
            await interaction.followup.send("請選擇要移除的標的：", view=view)

    # --- 內部邏輯：更新清單訊息 ---
    async def update_list_message(self, interaction: discord.Interaction, is_first=False):
        try:
            if is_first:
                # 斜線指令第一次呼叫
                await interaction.response.defer(thinking=True, ephemeral=True)
            else:
                # 按鈕觸發
                await interaction.response.defer(ephemeral=True)

            embed = discord.Embed(
                title=f"📊 {interaction.user.name} 的監控清單", 
                color=discord.Color.blue(),
                timestamp=datetime.now(TW_TIME)
            )
            
            with self.db_manager() as session:
                user = session.query(User).filter_by(discord_id=interaction.user.id).first()
                if not user or not user.stocks:
                    msg = "⚠️ 清單目前是空的。"

                    if is_first:
                        return await interaction.followup.send(msg, ephemeral=True)
                    else:
                        return await interaction.edit_original_response(content=msg, embed=None, view=None)

                # 遍歷股票
                for s in user.stocks:
                    async with self.api_lock:
                        info = get_stock_snapshot(s.stock_symbol, self.api_token)
                    
                    price = info['price'] if info else "N/A"
                    change_pct = info['change_pct'] if info else 0
                    emoji = "🔺" if change_pct > 0 else "🟢" if change_pct < 0 else "⚪"
                    
                    roi_str = ""
                    if info and s.buy_price:
                        roi = ((price - s.buy_price) / s.buy_price) * 100
                        roi_str = f"\n總損益: {'📈' if roi>=0 else '📉'} `{roi:.2f}%`"
                    
                    embed.add_field(
                        name=f"{s.stock_name} ({s.stock_symbol})", 
                        value=f"現價: `{price}` ({emoji}{change_pct:.2f}%)\n成本: `{s.buy_price or 'N/A'}`{roi_str}", 
                        inline=False
                    )
                    # 查詢完休息，避免 Fugle API 報錯
                    await asyncio.sleep(0.5) 

            # 統一更新訊息
            view = StockListView(self, interaction.user.id)
            await interaction.edit_original_response(content=None, embed=embed, view=view)

        except Exception as e:
            print(f"❌ 更新列表失敗: {e}")
            try:
                await interaction.followup.send("更新資料時發生錯誤，請稍後再試。", ephemeral=True)
            except:
                pass

    async def send_dm(self, user_id, content=None, embed=None):
        try:
            user = await self.bot.fetch_user(user_id)
            if user: await user.send(content=content, embed=embed)
        except Exception as e:
            print(f"無法發送私訊給 {user_id}: {e}")

async def setup(bot):
    db_manager = getattr(bot, "db_session", None)
    await bot.add_cog(Stock(bot, db_manager))
