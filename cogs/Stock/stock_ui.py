import discord
from discord import ui
from .utils.fugle_api import get_stock_snapshot

try:
    from cogs.System.ui.buttons import BackToMainButton
except ImportError:
    print("⚠️ 警告：找不到 BackToMainButton，請檢查路徑是否正確")
    BackToMainButton = None


class StockAddModal(ui.Modal, title='新增台股監控'):
    symbol = ui.TextInput(label='股票代號', placeholder='例如: 2330', min_length=4, max_length=6)
    buy_price = ui.TextInput(label='買入成本 (選填)', placeholder='不填則不計損益', required=False)
    up_percent = ui.TextInput(label='漲幅報警 % (選填)', placeholder='例如填 3 代表 3%', required=False)
    down_percent = ui.TextInput(label='跌幅報警 % (選填)', placeholder='例如填 -2 代表 -2%', required=False)

    def __init__(self, db_manager, api_token, api_lock):
        super().__init__()
        self.db_manager = db_manager
        self.api_token = api_token
        self.api_lock = api_lock

    async def on_submit(self, interaction: discord.Interaction):
        from database.models import UserStockWatch, User # 避免循環匯入
        await interaction.response.defer(thinking=True, ephemeral=True)

        sym = self.symbol.value.strip()
        # 轉換數值
        price = float(self.buy_price.value) if self.buy_price.value else None
        up = float(self.up_percent.value) / 100 if self.up_percent.value else None
        down = float(self.down_percent.value) / 100 if self.down_percent.value else None

        async with self.api_lock:
            info = get_stock_snapshot(sym, self.api_token)

        if not info:
            return await interaction.followup.send(f"❌ 找不到股票 `{sym}`")

        with self.db_manager() as session:
            user = session.query(User).filter_by(discord_id=interaction.user.id).first()
            if not user:
                user = User(discord_id=interaction.user.id, username=interaction.user.name)
                session.add(user)
                session.flush()

            # 檢查是否重複，重複則更新
            watch = session.query(UserStockWatch).filter_by(user_id=interaction.user.id, stock_symbol=sym).first()
            if watch:
                watch.buy_price, watch.target_up, watch.target_down = price, up, down
            else:
                session.add(UserStockWatch(user_id=interaction.user.id, stock_symbol=sym, 
                                          stock_name=info['name'], buy_price=price, 
                                          target_up=up, target_down=down))
            session.commit()

        await interaction.followup.send(f"✅ 已成功監控 **{info['name']} ({sym})**", ephemeral=True)

class StockRemoveSelect(ui.Select):
    def __init__(self, stocks, db_manager):
        options = [
            discord.SelectOption(label=f"{s.stock_name} ({s.stock_symbol})", value=s.stock_symbol)
            for s in stocks
        ]
        super().__init__(placeholder="請選擇要移除的股票...", options=options)
        self.db_manager = db_manager

    async def callback(self, interaction: discord.Interaction):
        from database.models import UserStockWatch
        with self.db_manager() as session:
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
        await interaction.response.send_modal(StockAddModal(self.cog.db_manager, self.cog.api_token, self.cog.api_lock))

    @ui.button(label="移除股票監控", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_stock_btn(self, interaction: discord.Interaction, button: ui.Button):
        # 呼叫刪除選單
        await interaction.response.defer(ephemeral=True)
        with self.cog.db_manager() as session:
            from database.models import User, UserStockWatch
            user = session.query(User).filter_by(discord_id=interaction.user.id).first()
            if not user or not user.stocks:
                return await interaction.followup.send("⚠️ 你的清單目前是空的。", ephemeral=True)
            
            view = ui.View()
            view.add_item(StockRemoveSelect(user.stocks, self.cog.db_manager))
            await interaction.followup.send("請選擇要移除的標的：", view=view, ephemeral=True)