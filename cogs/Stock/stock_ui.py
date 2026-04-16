import discord
from discord import ui
from .utils.fugle_api import get_stock_snapshot

try:
    from cogs.System.ui.buttons import BackToMainButton
except ImportError:
    print("⚠️ 警告：找不到 BackToMainButton，請檢查路徑是否正確")
    BackToMainButton = None


class StockAddModal(ui.Modal, title='新增/更新精確監控'):
    # 股票代號
    symbol = ui.TextInput(label='股票代號', placeholder='例如: 2330', min_length=4, max_length=6)
    # 持有股數 (整數)
    shares = ui.TextInput(label='持有股數 (選填)', placeholder='例如: 1000', required=False)
    # 總付出成本 (含手續費)
    total_cost = ui.TextInput(label='總付出成本 (選填, 含手續費)', placeholder='例如: 500285', required=False)
    # 漲幅預警
    up_percent = ui.TextInput(label='漲幅報警 % (選填)', placeholder='例如填 3 代表 3%', required=False)
    # 跌幅報警
    down_percent = ui.TextInput(label='跌幅報警 % (選填)', placeholder='例如填 -2 代表 -2%', required=False)

    def __init__(self, SessionLocal, api_token, api_lock):
        super().__init__()
        self.SessionLocal = SessionLocal
        self.api_token = api_token
        self.api_lock = api_lock

    async def on_submit(self, interaction: discord.Interaction):
        from database.models import UserStockWatch, User
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            sym = self.symbol.value.strip()
            
            num_shares = int(self.shares.value) if self.shares.value and self.shares.value.isdigit() else 0
            cost_val = float(self.total_cost.value) if self.total_cost.value else 0.0
            
            # 自動推算單價 (用於顯示或舊邏輯相容)
            avg_buy_price = cost_val / num_shares if num_shares > 0 else None
            
            up = float(self.up_percent.value) / 100 if self.up_percent.value else None
            down = float(self.down_percent.value) / 100 if self.down_percent.value else None

            # 串接 API 確認股票存在
            async with self.api_lock:
                info = get_stock_snapshot(sym, self.api_token)

            if not info:
                return await interaction.followup.send(f"❌ 找不到股票 `{sym}`", ephemeral=True)

            with self.SessionLocal() as session:
                user = session.query(User).filter_by(discord_id=interaction.user.id).first()
                if not user:
                    user = User(discord_id=interaction.user.id, username=interaction.user.name)
                    session.add(user)
                    session.flush()

                # 檢查是否重複，重複則更新，不重複則新增 (Upsert 邏輯)
                watch = session.query(UserStockWatch).filter_by(user_id=interaction.user.id, stock_symbol=sym).first()
                
                if watch:
                    watch.shares = num_shares
                    watch.total_cost = cost_val
                    watch.buy_price = avg_buy_price # 同步更新單價
                    watch.target_up = up
                    watch.target_down = down
                    status_msg = "更新"
                else:
                    session.add(UserStockWatch(
                        user_id=interaction.user.id, 
                        stock_symbol=sym, 
                        stock_name=info['name'], 
                        shares=num_shares, 
                        total_cost=cost_val,
                        buy_price=avg_buy_price,
                        target_up=up, 
                        target_down=down
                    ))
                    status_msg = "新增"
                
                session.commit()

            await interaction.followup.send(f"✅ 已成功{status_msg} **{info['name']} ({sym})** 的精確監控", ephemeral=True)

        except ValueError:
            await interaction.followup.send("❌ 輸入格式錯誤，請確保股數為整數、成本與比例為數字。", ephemeral=True)
        except Exception as e:
            print(f"Modal Submit Error: {e}")
            await interaction.followup.send(f"❌ 發生未知錯誤: {e}", ephemeral=True)

class StockRemoveSelect(ui.Select):
    def __init__(self, stocks, SessionLocal):
        options = [
            discord.SelectOption(label=f"{s.stock_name} ({s.stock_symbol})", value=s.stock_symbol)
            for s in stocks
        ]
        super().__init__(placeholder="請選擇要移除的股票...", options=options)
        self.SessionLocal = SessionLocal

    async def callback(self, interaction: discord.Interaction):
        from database.models import UserStockWatch
        with self.SessionLocal() as session:
            watch = session.query(UserStockWatch).filter_by(
                user_id=interaction.user.id, stock_symbol=self.values[0]).first()
            if watch:
                name = watch.stock_name
                session.delete(watch)
                session.commit()
                await interaction.response.send_message(f"✅ 已成功移除 **{name}**", ephemeral=True)
            else:
                await interaction.response.send_message("❌ 找不到該紀錄", ephemeral=True)

class StockListView(ui.View):
    def __init__(self, cog, interaction_user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = interaction_user_id

    @ui.button(label="🔄 重新整理(若list中太多股票 將會處理較久)", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, button: ui.Button):
        # 權限檢查
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("這不是你的選單！", ephemeral=True)
        
        await self.cog.update_list_message(interaction, is_first=False)

class StockDashboardView(ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.bot = bot
        self.cog = cog

        if BackToMainButton:
            self.add_item(BackToMainButton(self.bot))


    @ui.button(label="查看監控清單", style=discord.ButtonStyle.success, emoji="📋")
    async def view_list(self, interaction: discord.Interaction, button: ui.Button):
        await self.cog.update_list_message(interaction, is_first=True)

    @ui.button(label="新增股票監控", style=discord.ButtonStyle.primary, emoji="➕")
    async def add_stock_btn(self, interaction: discord.Interaction, button: ui.Button):
        # Modal 須用 send_modal
        await interaction.response.send_modal(StockAddModal(self.cog.SessionLocal, self.cog.api_token, self.cog.api_lock))

    @ui.button(label="移除股票監控", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_stock_btn(self, interaction: discord.Interaction, button: ui.Button):
        # 呼叫刪除選單
        await interaction.response.defer(ephemeral=True)
        with self.cog.SessionLocal() as session:
            from database.models import User, UserStockWatch
            user = session.query(User).filter_by(discord_id=interaction.user.id).first()
            if not user or not user.stocks:
                return await interaction.followup.send("⚠️ 你的清單目前是空的。", ephemeral=True)
            
            view = ui.View()
            view.add_item(StockRemoveSelect(user.stocks, self.cog.SessionLocal))
            await interaction.followup.send("請選擇要移除的標的：", view=view, ephemeral=True)