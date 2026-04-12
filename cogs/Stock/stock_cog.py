import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
from datetime import datetime, timedelta, timezone, time
from .utils.fugle_api import get_stock_snapshot
from database.models import UserStockWatch, User
from .stock_ui import StockAddModal, StockRemoveSelect, StockListView, ui

# 💡 定義台灣時區 (UTC+8)
TW_TIME = timezone(timedelta(hours=8))
REPORT_TIME = time(hour=13, minute=45, tzinfo=TW_TIME)

import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
from datetime import datetime, timedelta, timezone, time
from .utils.fugle_api import get_stock_snapshot
from database.models import UserStockWatch, User
# 💡 確保匯入你剛寫好的 UI 組件
from .stock_ui import StockAddModal, StockRemoveSelect, StockListView, ui

# 定義台灣時區
TW_TIME = timezone(timedelta(hours=8))
REPORT_TIME = time(hour=13, minute=45, tzinfo=TW_TIME)

class Stock(commands.Cog):
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager # ✨ 核心：確保屬性被正確賦值
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
            # 💡 修改重點：在 defer 時就加入 ephemeral=True
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
                    # 💡 這裡的 followup 也要確保私密 (雖然 defer 設定了通常會繼承，但加上去最保險)
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
                    # 查詢完休息一下，避免 Fugle API 報錯
                    await asyncio.sleep(0.5) 

            # 最後統一更新訊息
            view = StockListView(self, interaction.user.id)
            # 因為已經 defer(ephemeral=True) 了，這裡更新出來的一定是私密訊息
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

# class Stock(commands.Cog):
#     def __init__(self, bot, db_manager):
#         self.bot = bot
#         self.db_manager = db_manager
#         self.api_token = os.getenv("FUGLE_TOKEN")
        
#         # ✨ 新增：API 專用鎖，確保同一時間只有一個請求，並允許使用者指令「插隊」
#         self.api_lock = asyncio.Lock() 
        
#         # 啟動背景監控任務
#         self.stock_monitor.start()
#         self.market_report.start()

#     def cog_unload(self):
#         # 當 Cog 被卸載時，停止任務避免報錯
#         self.stock_monitor.cancel()
#         self.market_report.cancel()

#     # --- 背景監控任務 ---
#     @tasks.loop(minutes=1)
#     async def stock_monitor(self):
#         """ 每分鐘啟動一輪巡邏，但在每一支股票間休息 1 秒 """
#         now = datetime.now(TW_TIME)
        
#         # 1. 判斷是否為台股交易日 (週一至週五) 與交易時段 (09:00 - 13:35)
#         if now.weekday() >= 5: return 
#         current_time_val = now.hour * 100 + now.minute
#         if not (900 <= current_time_val <= 1335):
#             return

#         print(f"[{now.strftime('%H:%M:%S')}] 啟動新一輪股票巡邏 (台北時區)...")

#         with self.db_manager() as session:
#             watches = session.query(UserStockWatch).all()
            
#             for watch in watches:
#                 # 💡 背景任務：在執行 API 請求前先獲取鎖
#                 async with self.api_lock:
#                     try:
#                         info = get_stock_snapshot(watch.stock_symbol, self.api_token)
                        
#                         if info and info['price'] is not None:
#                             curr_price = info['price']
#                             change_pct = info['change_pct']

#                             # 統一轉成小數來比對
#                             real_change = change_pct / 100 if abs(change_pct) > 1 else change_pct
                            
#                             msg = None
#                             if real_change >= watch.target_up:
#                                 msg = f"🚀 **{info['name']} ({watch.stock_symbol})** 噴發中！\n現價：`{curr_price}` (漲幅：`{real_change*100:.2f}%`)"
#                             elif real_change <= watch.target_down:
#                                 msg = f"📉 **{info['name']} ({watch.stock_symbol})** 正在下跌！\n現價：`{curr_price}` (跌幅：`{real_change*100:.2f}%`)"

#                             if msg and watch.last_notified_price != curr_price:
#                                 await self.send_dm(watch.user_id, msg)
#                                 watch.last_notified_price = curr_price
#                                 session.commit() 
#                     except Exception as e:
#                         print(f"監控 {watch.stock_symbol} 發生錯誤: {e}")

#                 # 💡 關鍵：每一支休息一秒。這段 sleep 時間「鎖」是放開的，使用者指令可以隨時插隊。
#                 await asyncio.sleep(1) 

#     # --- 每日收盤戰報任務 ---
#     @tasks.loop(time=REPORT_TIME)
#     async def market_report(self):
#         now = datetime.now(TW_TIME)
#         # 只有週一至週五發送報表
#         if now.weekday() >= 5:
#             return

#         print(f"[{now.strftime('%H:%M:%S')}] 正在生成每日收盤戰報...")

#         # 1. 從資料庫抓取所有監控資料並按 user_id 分組
#         user_reports = {} # {user_id: [watch1, watch2, ...]}
        
#         with self.db_manager() as session:
#             all_watches = session.query(UserStockWatch).all()
#             for watch in all_watches:
#                 if watch.user_id not in user_reports:
#                     user_reports[watch.user_id] = []
#                 user_reports[watch.user_id].append(watch)

#         # 2. 為每個使用者生成專屬報表
#         for user_id, watches in user_reports.items():
#             embed = discord.Embed(
#                 title=f"📊 收盤戰報 ({now.strftime('%m/%d')})",
#                 description="這是你今日監控清單的收盤表現總結：",
#                 color=discord.Color.gold(),
#                 timestamp=now
#             )
            
#             total_profit_loss = 0
#             has_cost_data = False

#             for s in watches:
#                 async with self.api_lock:
#                     info = get_stock_snapshot(s.stock_symbol, self.api_token)
                
#                 if info:
#                     price = info['price']
#                     change_val = info.get('change', 0) # 漲跌點數
#                     change_pct = info['change_pct']
                    
#                     # 格式化漲跌符號
#                     emoji = "🔴" if change_pct > 0 else "🟢" if change_pct < 0 else "⚪"
                    
#                     field_value = f"收盤價: `{price}` ({emoji}{change_pct:.2f}%)"
                    
#                     # 如果有買入成本，計算損益
#                     if s.buy_price:
#                         roi = ((price - s.buy_price) / s.buy_price) * 100
#                         roi_emoji = "📈" if roi >= 0 else "📉"
#                         field_value += f"\n累積損益: {roi_emoji} `{roi:.2f}%`"
#                         has_cost_data = True
                    
#                     embed.add_field(
#                         name=f"{s.stock_name} ({s.stock_symbol})",
#                         value=field_value,
#                         inline=False
#                     )

#             if not has_cost_data:
#                 embed.set_footer(text="提示：使用 /stock_add 時輸入買入價格，即可計算損益。")
            
#             # 3. 發送私訊
#             await self.send_dm(user_id, embed=embed)

#     # --- 斜線指令：新增監控 ---
#     @app_commands.command(name="stock_add", description="新增或更新台股監控")
#     async def stock_add(
#         self, 
#         interaction: discord.Interaction, 
#         symbol: str, 
#         buy_price: float = None,
#         up_percent: float = None,
#         down_percent: float = None
#     ):
#         await interaction.response.defer(thinking=True)

#         # 格式化代號與百分比
#         symbol = symbol.strip()
#         target_up = up_percent / 100 if up_percent is not None else None
#         target_down = down_percent / 100 if down_percent is not None else None

#         try:
#             async with self.api_lock:
#                 info = get_stock_snapshot(symbol, self.api_token)
            
#             if not info:
#                 return await interaction.followup.send(f"❌ 找不到股票代號 `{symbol}`")

#             with self.db_manager() as session:
#                 # 1. 先確認使用者是否存在
#                 user = session.query(User).filter_by(discord_id=interaction.user.id).first()
#                 if not user:
#                     user = User(discord_id=interaction.user.id, username=interaction.user.name)
#                     session.add(user)
#                     session.flush()

#                 # 💡 2. 檢查該使用者是否已經監控了這支股票
#                 existing_watch = session.query(UserStockWatch).filter_by(
#                     user_id=interaction.user.id, 
#                     stock_symbol=symbol
#                 ).first()

#                 if existing_watch:
#                     # ✨ 若已存在，則更新原有紀錄 (覆蓋)
#                     existing_watch.buy_price = buy_price
#                     existing_watch.target_up = target_up
#                     existing_watch.target_down = target_down
#                     existing_watch.stock_name = info['name'] # 更新一下名稱 (預防改名)
#                     action_text = "更新"
#                 else:
#                     # ✨ 若不存在，才建立新紀錄
#                     new_watch = UserStockWatch(
#                         user_id=interaction.user.id,
#                         stock_symbol=symbol,
#                         stock_name=info['name'],
#                         buy_price=buy_price,
#                         target_up=target_up,
#                         target_down=target_down
#                     )
#                     session.add(new_watch)
#                     action_text = "新增"

#                 session.commit()

#             # 建立回覆訊息
#             monitor_status = []
#             if up_percent: monitor_status.append(f"📈 漲幅 > {up_percent}%")
#             if down_percent: monitor_status.append(f"📉 跌幅 < {down_percent}%")
#             alert_text = " / ".join(monitor_status) if monitor_status else "🚫 僅查詢，不監控通知"

#             embed = discord.Embed(title=f"✅ 監控{action_text}成功", color=discord.Color.green())
#             embed.add_field(name="股票", value=f"{info['name']} ({symbol})", inline=True)
#             embed.add_field(name="目前現價", value=f"{info['price']}", inline=True)
#             embed.add_field(name="監控狀態", value=f"`{alert_text}`", inline=False)
            
#             await interaction.followup.send(embed=embed)

#         except Exception as e:
#             print(f"❌ stock_add 失敗: {e}")
#             await interaction.followup.send(f"❌ 系統錯誤: {e}")

#     # --- 背景監控任務 (修改報警判斷) ---
#     @tasks.loop(minutes=1)
#     async def stock_monitor(self):
#         # ... (前面的時區判斷邏輯相同) ...
        
#         with self.db_manager() as session:
#             watches = session.query(UserStockWatch).all()
#             for watch in watches:
#                 # 💡 如果上下限都是 None，代表這支純查詢，直接跳過 API 請求節省額度
#                 if watch.target_up is None and watch.target_down is None:
#                     continue

#                 async with self.api_lock:
#                     try:
#                         info = get_stock_snapshot(watch.stock_symbol, self.api_token)
#                         if info and info['price'] is not None:
#                             curr_price = info['price']
#                             change_pct = info['change_pct']
#                             real_change = change_pct / 100 if abs(change_pct) > 1 else change_pct
                            
#                             msg = None
#                             # ✨ 關鍵修改：只有在「有設定門檻」的情況下才判斷
#                             if watch.target_up is not None and real_change >= watch.target_up:
#                                 msg = f"🚀 **{info['name']} ({watch.stock_symbol})** 噴發！\n現價：`{curr_price}` (漲：`{real_change*100:.2f}%`)"
#                             elif watch.target_down is not None and real_change <= watch.target_down:
#                                 msg = f"📉 **{info['name']} ({watch.stock_symbol})** 下跌！\n現價：`{curr_price}` (跌：`{real_change*100:.2f}%`)"

#                             if msg and watch.last_notified_price != curr_price:
#                                 await self.send_dm(watch.user_id, msg)
#                                 watch.last_notified_price = curr_price
#                                 session.commit()
#                     except Exception as e:
#                         print(f"監控錯誤: {e}")
                
#                 await asyncio.sleep(1)

#     # --- 斜線指令：查看清單 ---
#     @app_commands.command(name="stock_list", description="查看我的股票監控清單與即時損益")
#     async def stock_list(self, interaction: discord.Interaction):
#         await interaction.response.defer(thinking=True)

#         with self.db_manager() as session:
#             user = session.query(User).filter_by(discord_id=interaction.user.id).first()
#             if not user or not user.stocks:
#                 return await interaction.followup.send("⚠️ 你的監控清單目前是空的。")

#             embed = discord.Embed(title=f"📊 {interaction.user.name} 的監控清單", color=discord.Color.blue())
            
#             for s in user.stocks:
#                 # 💡 查詢每一支目前的價格 (同樣使用插隊鎖)
#                 async with self.api_lock:
#                     info = get_stock_snapshot(s.stock_symbol, self.api_token)
                
#                 price_str = f"`{info['price']}`" if info else "查詢失敗"
                
#                 # 計算損益 (如果有買入價)
#                 roi_str = ""
#                 if info and s.buy_price:
#                     roi = ((info['price'] - s.buy_price) / s.buy_price) * 100
#                     emoji = "📈" if roi >= 0 else "📉"
#                     roi_str = f"\n預估損益: {emoji} `{roi:.2f}%`"

#                 embed.add_field(
#                     name=f"{s.stock_name} ({s.stock_symbol})",
#                     value=f"現價: {price_str} / 成本: `{s.buy_price or 'N/A'}`{roi_str}",
#                     inline=False
#                 )

#             await interaction.followup.send(embed=embed)
            
#     # --- 斜線指令：刪除監控 ---
#     @app_commands.command(name="stock_remove", description="從清單中移除指定的股票")
#     @app_commands.describe(symbol="要移除的股票代號 (如: 2330)")
#     async def stock_remove(self, interaction: discord.Interaction, symbol: str):
#         await interaction.response.defer(thinking=True)
        
#         # 統一格式化輸入內容
#         symbol = symbol.strip()

#         try:
#             with self.db_manager() as session:
#                 # 1. 尋找該使用者名下對應代號的紀錄
#                 watch = session.query(UserStockWatch).filter_by(
#                     user_id=interaction.user.id, 
#                     stock_symbol=symbol
#                 ).first()
                
#                 # 2. 如果找不到，回報錯誤
#                 if not watch:
#                     return await interaction.followup.send(f"⚠️ 在你的清單中找不到股票代號 `{symbol}`。")

#                 stock_name = watch.stock_name
                
#                 # 3. 執行刪除
#                 session.delete(watch)
#                 session.commit()
                
#             # 4. 回傳成功訊息
#             await interaction.followup.send(f"✅ 已成功移除 **{stock_name} ({symbol})**。")
#             print(f"DEBUG: {interaction.user.name} 已刪除股票 {symbol}")

#         except Exception as e:
#             print(f"❌ stock_remove 失敗: {e}")
#             await interaction.followup.send(f"❌ 刪除時發生系統錯誤: {e}")

#     # --- 工具函式 ---
#     async def send_dm(self, user_id, content=None, embed=None):
#         try:
#             user = await self.bot.fetch_user(user_id)
#             if user:
#                 await user.send(content=content, embed=embed)
#         except Exception as e:
#             print(f"無法發送私訊給 {user_id}: {e}")

async def setup(bot):
    db_manager = getattr(bot, "db_session", None)
    await bot.add_cog(Stock(bot, db_manager))